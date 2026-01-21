import calendar
import json
import traceback
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from django.db import transaction
from django.db.models import F, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.contrib import messages

from core import mixins
from transactions import filters, tables
from transactions.utils import generate_next_voucher_number

from . import forms
from .models import IncomeExpense, Transaction, TransactionEntry, ContraVoucher
# Assuming GroupMaster is imported from accounting.models or similar in your full project, 
# though it wasn't explicitly in the import list of the snippet, it's used in the code.
from accounting.models import Account, GroupMaster 

logger = logging.getLogger(__name__)


def load_party_accounts(request):
    branch_id = request.GET.get('branch')
    is_contra = request.GET.get('is_contra') == 'true'
    data = []

    if branch_id:
        accounts = Account.objects.filter(branch_id=branch_id, is_active=True)

        if is_contra:
            # Strictly filter for Cash and Bank hierarchies
            valid_keys = ["CASH_ACCOUNT", "BANK_ACCOUNT"]
            base_groups = GroupMaster.objects.filter(locking_group__in=valid_keys)
            
            allowed_group_ids = set()
            for g in base_groups:
                allowed_group_ids.update(g.get_descendants(include_self=True).values_list('id', flat=True))
            
            # Filter accounts strictly under these groups
            accounts = accounts.filter(under_id__in=allowed_group_ids)

        accounts = accounts.select_related('under', 'branch')
        data = [{'id': a.id, 'name': f"{a.name} ({a.under.name if a.under else ''})"} for a in accounts]

    return JsonResponse(data, safe=False)


def load_accounts_by_branch(request):
    """
    API endpoint to load accounts based on selected branch and type
    Expected parameters:
    - branch_id: ID of the selected branch
    - type: Type of accounts to load ('income', 'expense', or 'party')
    """
    branch_id = request.GET.get('branch_id')
    account_type = request.GET.get('type', '').lower()
    data = []

    if branch_id and account_type:
        try:
            from django.db.models import Q
            from branches.models import Branch
            
            # Get the branch object
            branch = Branch.objects.filter(id=branch_id).first()
            
            # Start with branch filter
            accounts = Account.objects.filter(branch_id=branch_id, is_active=True)
            
            # Apply type-specific filters
            if account_type == 'income':
                # Filter for income accounts using utility functions
                from accounting.utils import get_direct_income_group_ids, get_indirect_income_group_ids
                if branch:
                    income_group_ids = get_direct_income_group_ids(branch) + get_indirect_income_group_ids(branch)
                    accounts = accounts.filter(under_id__in=income_group_ids)
            elif account_type == 'expense':
                # Filter for expense accounts using utility functions
                from accounting.utils import get_direct_expense_group_ids, get_indirect_expense_group_ids
                if branch:
                    expense_group_ids = get_direct_expense_group_ids(branch) + get_indirect_expense_group_ids(branch)
                    accounts = accounts.filter(under_id__in=expense_group_ids)
            elif account_type == 'party':
                # Check if 'is_gst' parameter is provided to determine if it's a party transaction
                is_party = request.GET.get('is_party', '').lower() in ['true', '1', 'yes']
                if is_party:
                    # If is_party is true, show Sundry Creditors and Sundry Debtors accounts
                    from accounting.utils import get_sundry_creditors_group_ids, get_sundry_debtors_group_ids
                    if branch:
                        party_group_ids = get_sundry_creditors_group_ids(branch) + get_sundry_debtors_group_ids(branch)
                        accounts = accounts.filter(under_id__in=party_group_ids)
                else:
                    # Otherwise show CUSTOMER/SUPPLIER ledger types
                    accounts = accounts.filter(ledger_type__in=['CUSTOMER', 'SUPPLIER'])
            elif account_type == 'payment':
                # Filter for payment accounts (BANK_ACCOUNT and CASH_ACCOUNT)
                accounts = accounts.filter(under__locking_group__in=['BANK_ACCOUNT', 'CASH_ACCOUNT'])
            
            accounts = accounts.select_related('under', 'branch')
            data = [{'id': a.id, 'name': str(a)} for a in accounts]
        except Exception as e:
            logger.error(f"Error loading accounts by branch: {str(e)}")
    
    return JsonResponse({'accounts': data}, safe=False)


def load_category_accounts(request):
    branch_id = request.GET.get('branch')
    txn_type = request.GET.get('type')  
    data = []

    if branch_id and txn_type:
        accounts = Account.objects.filter(
            branch_id=branch_id,
        ).select_related('under')

        data = [{'id': a.id, 'name': str(a)} for a in accounts]

    return JsonResponse(data, safe=False)


class TransactionMixin:
    """Mixin for transaction navigation and permission handling"""
    
    # Configuration for menu items
    menu_group_config = {
        'sales': [
            {"name": "Invoice", "prefix": "transactions:saleinvoice", "view_perm": "transactions.view_invoice", "add_perm": "transactions.add_invoice"},
            {"name": "Order", "prefix": "transactions:saleorder", "view_perm": "transactions.view_saleorder", "add_perm": "transactions.add_saleorder"},
            {"name": "Return", "prefix": "transactions:creditnote", "view_perm": "transactions.view_creditnote", "add_perm": "transactions.add_creditnote"},
        ],
        'purchases': [
            {"name": "Invoice", "prefix": "transactions:purchaseinvoice", "view_perm": "transactions.view_purchaseinvoice", "add_perm": "transactions.add_purchaseinvoice"},
            {"name": "Order", "prefix": "transactions:purchaseorder", "view_perm": "transactions.view_purchaseorder", "add_perm": "transactions.add_purchaseorder"},
            {"name": "Return", "prefix": "transactions:debitnote", "view_perm": "transactions.view_debitnote", "add_perm": "transactions.add_debitnote"},
        ],
        'entries': [
            {"name": "Receipts", "prefix": "transactions:receipt", "view_perm": "transactions.view_receiptpaymentvoucher", "add_perm": "transactions.add_receiptpaymentvoucher"},
            {"name": "Payments", "prefix": "transactions:payment", "view_perm": "transactions.view_payment", "add_perm": "transactions.add_payment"},
            {"name": "JV", "prefix": "transactions:journalvoucher", "view_perm": "transactions.view_transaction", "add_perm": "transactions.add_transaction"},
        ]
    }

    @cached_property
    def _menu_items(self) -> List[Dict]:
        """Define all possible menu items with their permissions"""
        return [
            # {"name": "Receipts", "link": reverse_lazy("transactions:receipt_list"), "permission": "transactions.view_receiptpaymentvoucher", "icon": "fas fa-download"},
            # {"name": "Payments", "link": reverse_lazy("transactions:payment_list"), "permission": "transactions.view_payment", "icon": "fas fa-upload"},
            {"name": "JV", "link": reverse_lazy("transactions:journalvoucher_list"), "permission": "transactions.view_transaction", "icon": "fas fa-exchange-alt"},
            {"name": "Income", "link": reverse_lazy("transactions:income_list"), "permission": "transactions.view_incomeexpense", "icon": "fas fa-plus-circle"},
            {"name": "Expense", "link": reverse_lazy("transactions:expense_list"), "permission": "transactions.view_incomeexpense", "icon": "fas fa-minus-circle"},
        ]
    
    def get_sub_menu_items(self) -> List[Dict]:
        """Override this in subclasses to return specific sub-menu items"""
        return self.menu_group_config.get('sales', [])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        current_path = self.request.path
        
        # Filter menu items by permission
        context['btn_groups'] = [
            {
                **item,
                'active': str(item['link']) == current_path or current_path.startswith(str(item['link']))
            }
            for item in self._menu_items
            if user.has_perm(item['permission'])
        ]
        
        # Filter and generate sub-menu links
        context["btn_sub_groups"] = [
            {
                "name": item["name"],
                "list_link": reverse_lazy(f"{item['prefix']}_list"),
                "has_add_perm": user.has_perm(item['add_perm']),
                "create_link": reverse_lazy(f"{item['prefix']}_create") if user.has_perm(item['add_perm']) else None
            }
            for item in self.get_sub_menu_items()
            if user.has_perm(item['view_perm'])
        ]
        
        return context

    
class IncomeExpenseMixin(TransactionMixin):
    def get_sub_menu_items(self) -> List[Dict]:
        return [
            {"name": "Income", "prefix": "transactions:income", "view_perm": "transactions.view_incomeexpense", "add_perm": "transactions.add_incomeexpense"},
            {"name": "Expense", "prefix": "transactions:expense", "view_perm": "transactions.view_incomeexpense", "add_perm": "transactions.add_incomeexpense"},
        ]


def get_account_by_locking_type(locking_account_type, branch=None, transaction_type=None):
    """
    Get account by locking type.
    """
    # Adjust locking type for GST accounts based on transaction type
    if transaction_type and locking_account_type in ['CGST_PAYABLE', 'SGST_PAYABLE', 'IGST_PAYABLE']:
        if transaction_type == 'expense':
            # Expense uses RECEIVABLE (input tax credit)
            locking_account_type = locking_account_type.replace('PAYABLE', 'RECEIVABLE')
    
    try:
        # 1. Try to find branch-specific account
        return Account.objects.get(
            locking_account=locking_account_type,
            branch=branch
        )
    except Account.DoesNotExist:
        # 2. Fallback: Get the first available account of this type (Global/Other branch)
        account = Account.objects.filter(locking_account=locking_account_type).first()
        if not account:
            raise ValidationError(f"{locking_account_type} account not found. Please configure system accounts.")
        return account
    except Account.MultipleObjectsReturned:
        # 3. If multiple found for this branch, return the first
        return Account.objects.filter(
            locking_account=locking_account_type,
            branch=branch
        ).first()


def create_transaction_entry(transaction, account, debit_amount, credit_amount, description, creator):
    """
    Create a transaction entry (Line Item)
    """
    if not account:
        raise ValidationError(f"Account required for: {description}")
    
    if not hasattr(account, 'pk') or not account.pk:
        raise ValidationError(f"Invalid account for: {description}")
    
    # REMOVED 'branch' and 'company' from here as they are not in the TransactionEntry model
    return TransactionEntry.objects.create(
        transaction=transaction,
        account=account,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        description=description,
        creator=creator
    )

def create_gst_entry(transaction, account_type, amount, entry_type, description_prefix, branch, transaction_type, creator):
    """
    Create GST accounting entry
    """
    account = get_account_by_locking_type(
        account_type, 
        branch=branch, 
        transaction_type=transaction_type
    )
    
    debit = amount if entry_type == 'DR' else Decimal('0.00')
    credit = amount if entry_type == 'CR' else Decimal('0.00')
    
    create_transaction_entry(
        transaction=transaction,
        account=account,
        debit_amount=debit,
        credit_amount=credit,
        description=f"{description_prefix} (Voucher: {transaction.voucher_number})",
        creator=creator
    )


def create_rounding_entry(transaction, round_off_amount, transaction_type, branch, creator):
    """
    Create rounding off accounting entry
    """
    rounding_account = get_account_by_locking_type(
        'ROUNDING_OFF',
        branch=branch
    )
    
    if round_off_amount > 0:
        if transaction_type == 'income':
            debit, credit = Decimal('0.00'), abs(round_off_amount)
        else:
            debit, credit = abs(round_off_amount), Decimal('0.00')
    else:
        if transaction_type == 'income':
            debit, credit = abs(round_off_amount), Decimal('0.00')
        else:
            debit, credit = Decimal('0.00'), abs(round_off_amount)
    
    create_transaction_entry(
        transaction=transaction,
        account=rounding_account,
        debit_amount=debit,
        credit_amount=credit,
        description=f"Rounding off (Voucher: {transaction.voucher_number})",
        creator=creator
    )



def calculate_payment_total_from_entries(transaction, transaction_type):
    """
    Calculate total payments from existing transaction entries
    
    Args:
        transaction: Transaction instance
        transaction_type: 'income' or 'expense'
    
    Returns:
        Decimal total payment amount
    """
    payment_entries = TransactionEntry.objects.filter(
        transaction=transaction,
        account__under__locking_group__in=['BANK_ACCOUNT', 'CASH_ACCOUNT']
    )
    
    if transaction_type == 'income':
        # Income: payments are debits to bank/cash
        return sum(entry.debit_amount for entry in payment_entries)
    else:
        # Expense: payments are credits to bank/cash
        return sum(entry.credit_amount for entry in payment_entries)


def create_income_accounting_entries(instance, transaction_type, branch, creator):
    """
    Create all accounting entries for income transactions
    """
    transaction = instance.transaction
    
    # Extract amounts
    taxable_amount = instance.taxable_amount or Decimal('0.00')
    cgst_amount = instance.cgst_amount or Decimal('0.00')
    sgst_amount = instance.sgst_amount or Decimal('0.00')
    igst_amount = instance.igst_amount or Decimal('0.00')
    discount_amount = instance.discount_amount or Decimal('0.00')
    round_off_amount = instance.round_off_amount or Decimal('0.00')
    invoice_amount = transaction.invoice_amount or Decimal('0.00')

    # Calculate paid and unpaid amounts
    total_paid = calculate_payment_total_from_entries(transaction, transaction_type)
    unpaid_amount = invoice_amount - total_paid

    # Entry 1: CR Income Category
    category_amount = taxable_amount if instance.is_gst else (invoice_amount - round_off_amount)
    if category_amount > 0:
        create_transaction_entry(
            transaction=transaction,
            account=instance.category,
            debit_amount=Decimal('0.00'),
            credit_amount=category_amount,
            description=f"Income - {instance.category.name} (Voucher: {transaction.voucher_number})",
            creator=creator
        )

    # Entry 2: DR Discount
    if discount_amount > 0:
        discount_account = get_account_by_locking_type('SALES_DISCOUNT', branch=branch)
        create_transaction_entry(
            transaction=transaction,
            account=discount_account,
            debit_amount=discount_amount,
            credit_amount=Decimal('0.00'),
            description=f"Discount allowed (Voucher: {transaction.voucher_number})",
            creator=creator
        )

    # Entry 3-5: CR GST Accounts
    if instance.is_gst:
        if cgst_amount > 0:
            create_gst_entry(transaction, 'CGST_PAYABLE', cgst_amount, 'CR', 'CGST collected', 
                           branch, transaction_type, creator)
        if sgst_amount > 0:
            create_gst_entry(transaction, 'SGST_PAYABLE', sgst_amount, 'CR', 'SGST collected',
                           branch, transaction_type, creator)
        if igst_amount > 0:
            create_gst_entry(transaction, 'IGST_PAYABLE', igst_amount, 'CR', 'IGST collected',
                           branch, transaction_type, creator)

    # Entry 6: Rounding Off
    if round_off_amount != 0:
        create_rounding_entry(transaction, round_off_amount, transaction_type, branch, creator)

    # Entry 7: DR Party (only unpaid amount)
    if instance.party and hasattr(instance.party, 'pk') and instance.party.pk and unpaid_amount > 0:
        create_transaction_entry(
            transaction=transaction,
            account=instance.party,
            debit_amount=unpaid_amount,
            credit_amount=Decimal('0.00'),
            description=f"Receivable from {instance.party.name} (Voucher: {transaction.voucher_number})",
            creator=creator
        )



def create_expense_accounting_entries(instance, transaction_type, branch, creator):
    """
    Create all accounting entries for expense transactions
    """
    transaction = instance.transaction
    
    taxable_amount = instance.taxable_amount or Decimal('0.00')
    cgst_amount = instance.cgst_amount or Decimal('0.00')
    sgst_amount = instance.sgst_amount or Decimal('0.00')
    igst_amount = instance.igst_amount or Decimal('0.00')
    discount_amount = instance.discount_amount or Decimal('0.00')
    round_off_amount = instance.round_off_amount or Decimal('0.00')
    invoice_amount = transaction.invoice_amount or Decimal('0.00')

    total_paid = calculate_payment_total_from_entries(transaction, transaction_type)
    unpaid_amount = invoice_amount - total_paid

    # Entry 1: DR Expense Category
    category_amount = taxable_amount if instance.is_gst else (invoice_amount - round_off_amount)
    if category_amount > 0:
        create_transaction_entry(
            transaction=transaction,
            account=instance.category,
            debit_amount=category_amount,
            credit_amount=Decimal('0.00'),
            description=f"Expense - {instance.category.name} (Voucher: {transaction.voucher_number})",
            creator=creator
        )

    # Entry 2: CR Discount
    if discount_amount > 0:
        discount_account = get_account_by_locking_type('PURCHASE_DISCOUNT', branch=branch)
        create_transaction_entry(
            transaction=transaction,
            account=discount_account,
            debit_amount=Decimal('0.00'),
            credit_amount=discount_amount,
            description=f"Discount received (Voucher: {transaction.voucher_number})",
            creator=creator
        )

    # Entry 3-5: DR GST Accounts
    if instance.is_gst:
        if cgst_amount > 0:
            create_gst_entry(transaction, 'CGST_RECEIVABLE', cgst_amount, 'DR', 'CGST paid',
                           branch, transaction_type, creator)
        if sgst_amount > 0:
            create_gst_entry(transaction, 'SGST_RECEIVABLE', sgst_amount, 'DR', 'SGST paid',
                           branch, transaction_type, creator)
        if igst_amount > 0:
            create_gst_entry(transaction, 'IGST_RECEIVABLE', igst_amount, 'DR', 'IGST paid',
                           branch, transaction_type, creator)

    # Entry 6: Rounding Off
    if round_off_amount != 0:
        create_rounding_entry(transaction, round_off_amount, transaction_type, branch, creator)

    # Entry 7: CR Party (only unpaid amount)
    if instance.party and hasattr(instance.party, 'pk') and instance.party.pk and unpaid_amount > 0:
        create_transaction_entry(
            transaction=transaction,
            account=instance.party,
            debit_amount=Decimal('0.00'),
            credit_amount=unpaid_amount,
            description=f"Payable to {instance.party.name} (Voucher: {transaction.voucher_number})",
            creator=creator
        )



def create_payment_entries(payment_formset, transaction, income_expense, transaction_type, creator):
    """
    Create payment accounting entries from payment formset
    
    Args:
        payment_formset: Payment formset instance
        transaction: Transaction instance
        income_expense: IncomeExpense instance
        transaction_type: 'income' or 'expense'
        creator: User instance
    
    Returns:
        Decimal total payment amount
    """
    total_payment = Decimal('0.00')
    
    for form in payment_formset:
        if not form.cleaned_data or form.cleaned_data.get('DELETE'):
            continue
        
        amount = form.cleaned_data.get('amount', 0)
        payment_account = form.cleaned_data.get('account')
        
        if not amount or amount <= 0 or not payment_account:
            continue
        
        total_payment += Decimal(str(amount))
        
        # Get payment method description
        payment_method = "Unknown"
        if payment_account and hasattr(payment_account, 'under'):
            if hasattr(payment_account.under, 'locking_group'):
                if payment_account.under.locking_group == 'CASH_ACCOUNT':
                    payment_method = "Cash"
                elif payment_account.under.locking_group == 'BANK_ACCOUNT':
                    payment_method = "Bank"
                else:
                    payment_method = payment_account.name
        
        # Create entries based on transaction type
        if transaction_type == 'income':
            # DR Bank/Cash (receiving money)
            opposite = income_expense.party if income_expense.party else income_expense.category
            create_transaction_entry(
                transaction=transaction,
                account=payment_account,
                debit_amount=amount,
                credit_amount=Decimal('0.00'),
                description=f"Payment via {payment_account.name} for {opposite.name} (Voucher: {transaction.voucher_number})",
                creator=creator
            )
            
            # CR Party (if GST enabled and party exists)
            if income_expense.is_gst and income_expense.party:
                create_transaction_entry(
                    transaction=transaction,
                    account=income_expense.party,
                    debit_amount=Decimal('0.00'),
                    credit_amount=amount,
                    description=f"Payment received from {income_expense.party.name} via {payment_method} - {transaction.voucher_number}",
                    creator=creator
                )
        else:  # expense
            # CR Bank/Cash (paying money)
            opposite = income_expense.party if income_expense.party else income_expense.category
            create_transaction_entry(
                transaction=transaction,
                account=payment_account,
                debit_amount=Decimal('0.00'),
                credit_amount=amount,
                description=f"Payment via {payment_account.name} for {opposite.name} (Voucher: {transaction.voucher_number})",
                creator=creator
            )
            
            # DR Party (if GST enabled and party exists)
            if income_expense.is_gst and income_expense.party:
                create_transaction_entry(
                    transaction=transaction,
                    account=income_expense.party,
                    debit_amount=amount,
                    credit_amount=Decimal('0.00'),
                    description=f"Payment made to {income_expense.party.name} via {payment_method} - {transaction.voucher_number}",
                    creator=creator
                )
    
    return total_payment
    
    
class BaseTransactionCreateView(TransactionMixin, mixins.HybridCreateView):
    """Optimized base view for creating income and expense transactions"""
    model = IncomeExpense
    form_class = forms.IncomeExpenseForm
    exclude = None
    title = None
    url = None
    transaction_type = None
    template_name = "transactions/incomeexpense_form.html"
    inline_formset = forms.IncomeExpenseItemFormSet
    transaction_form_class = forms.TransactionForm
    auto_complete_formset_fields = False

    def get_success_url(self):
        """Redirect based on transaction type"""
        if self.transaction_type == 'income':
            return reverse_lazy('transactions:income_list')
        return reverse_lazy('transactions:expense_list')
    
    def get_auto_complete_custom_filters(self):
        try:
            branch = self.get_branch()
            filter_kwargs = {'branch': branch}
            
            direct_locking_group = "DIRECT_INCOME" if self.transaction_type == "income" else "DIRECT_EXPENSES"
            indirect_locking_group = "INDIRECT_INCOME" if self.transaction_type == "income" else "INDIRECT_EXPENSES"
            
            group_ids = []
            for locking_group in [direct_locking_group, indirect_locking_group]:
                group = GroupMaster.objects.filter(locking_group=locking_group, **filter_kwargs).first()
                if group:
                    group_ids.extend(group.get_descendants(include_self=True).values_list("id", flat=True))
        except Exception:
            group_ids = []

        return {
            "category": {"under__id__in": group_ids} if group_ids else {},
            "party": {"ledger_type__in": ("CUSTOMER", "SUPPLIER")}
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction_type'] = self.transaction_type
        context['transaction_form'] = self._get_transaction_form()
        
        payment_formset_class = (forms.PaymentOptionIncomeFormSet if self.transaction_type == 'income' 
                               else forms.PaymentOptionExpenseFormSet)
        
        context['payment_formset'] = payment_formset_class(
            self.request.POST or None,
            prefix='payments',
            form_kwargs={'branch': self.get_branch(), 'transaction_type': self.transaction_type}
        )
        
        from masters.models import State
        context['branch_state'] = State.objects.filter(is_active=True)
        return context
    
    def _get_transaction_form(self, prefix=None):
        form = self.transaction_form_class(
            self.request.POST or None,
            self.request.FILES or None,
            prefix=prefix,
            transaction_type=self.transaction_type
        )
        if not form.data:
            form.initial['voucher_number'] = self.get_next_voucher_number()
        
        if self.transaction_type == 'expense' and 'received_amount' in form.fields:
            form.fields['received_amount'].label = "Paid Amount"
        return form
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['transaction_type'] = self.transaction_type
        return kwargs
    
    def get_formset(self, custom_filters_map=None):
        if not self.inline_formset: return None
        return self.inline_formset(
            self.request.POST or None, 
            self.request.FILES or None, 
            instance=getattr(self, 'object', None),
            form_kwargs={'transaction_type': self.transaction_type, 'branch': self.get_branch()}
        )
    
    def get_next_voucher_number(self, lookup_field="voucher_number"):
        return generate_next_voucher_number(
            model=Transaction,
            branch=self.get_branch() or None,
            transaction_type=self.transaction_type,
            lookup_field=lookup_field
        )
    
    @transaction.atomic
    def form_valid(self, form):
        try:
            transaction_form = self._get_transaction_form()
            formset = self.get_formset()
            payment_formset_class = (forms.PaymentOptionIncomeFormSet if self.transaction_type == 'income' 
                                   else forms.PaymentOptionExpenseFormSet)
            payment_formset = payment_formset_class(
                self.request.POST,
                prefix='payments',
                form_kwargs={'branch': self.get_branch(), 'transaction_type': self.transaction_type}
            )

            if not (transaction_form.is_valid() and (not formset or formset.is_valid()) and (not payment_formset or payment_formset.is_valid())):
                return self.form_invalid(form, transaction_form=transaction_form, formset=formset, payment_formset=payment_formset)

            # --- SAVE TRANSACTION ---
            transaction_obj = transaction_form.save(commit=False)
            # Use the branch from the income expense form if available, otherwise from get_branch()
            if hasattr(form, 'cleaned_data') and 'branch' in form.cleaned_data and form.cleaned_data['branch']:
                transaction_obj.branch = form.cleaned_data['branch']
            else:
                transaction_obj.branch = self.get_branch()
            transaction_obj.creator = self.request.user
            transaction_obj.transaction_type = self.transaction_type
            
            # FIX: Manually assign status/is_active to bypass form validation issues
            transaction_obj.status = "posted"
            transaction_obj.is_active = True
            if not transaction_obj.priority: transaction_obj.priority = "normal"
            
            # Ensure unique voucher number
            if self._voucher_exists(transaction_obj.voucher_number):
                transaction_obj.voucher_number = self.get_next_voucher_number()
            transaction_obj.save()

            # --- SAVE INCOME/EXPENSE ---
            income_expense = form.save(commit=False)
            income_expense.transaction = transaction_obj
            income_expense.creator = self.request.user
            # Ensure branch is set from the form data
            if hasattr(form, 'cleaned_data') and 'branch' in form.cleaned_data and form.cleaned_data['branch']:
                income_expense.branch = form.cleaned_data['branch']
            elif not income_expense.branch_id:
                income_expense.branch = self.get_branch()
            income_expense.is_active = True # FIX
            income_expense.save()
            
            if formset:
                formset.instance = income_expense
                formset.save()

            # Entries creation
            if self.transaction_type == 'income':
                create_income_accounting_entries(income_expense, self.transaction_type, self.get_branch(), self.request.user)
            else:
                create_expense_accounting_entries(income_expense, self.transaction_type, self.get_branch(), self.request.user)

            if payment_formset and payment_formset.total_form_count() > 0:
                create_payment_entries(payment_formset, transaction_obj, income_expense, self.transaction_type, self.request.user)
            
            self.object = income_expense
            messages.success(self.request, f"{self.transaction_type.title()} created successfully.")
            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            print(f"TERMINAL ERROR: {str(e)}")
            messages.error(self.request, f"Submission failed: {str(e)}")
            return self.form_invalid(form)

    def _voucher_exists(self, voucher_number, exclude_pk=None):
        query = Transaction.objects.filter(voucher_number=voucher_number, transaction_type=self.transaction_type, branch=self.get_branch())
        if exclude_pk: query = query.exclude(pk=exclude_pk)
        return query.exists()

    def form_invalid(self, form, transaction_form=None, formset=None, payment_formset=None):
        if transaction_form is None: transaction_form = self._get_transaction_form()
        if formset is None: formset = self.get_formset()
        if payment_formset is None:
            payment_formset_class = (forms.PaymentOptionIncomeFormSet if self.transaction_type == 'income' else forms.PaymentOptionExpenseFormSet)
            payment_formset = payment_formset_class(self.request.POST, prefix='payments', form_kwargs={'branch': self.get_branch(), 'transaction_type': self.transaction_type})
        
        print("\n=== FORM VALIDATION FAILED ===")
        self._display_form_errors(form, 'Main Form')
        self._display_form_errors(transaction_form, 'Transaction Form')
        if formset: self._display_formset_errors(formset, 'Items Formset')
        if payment_formset: self._display_formset_errors(payment_formset, 'Payments Formset')
        print("==============================\n")

        return self.render_to_response(self.get_context_data(form=form, transaction_form=transaction_form, formset=formset, payment_formset=payment_formset))

    def _display_form_errors(self, form, form_name):
        if hasattr(form, 'errors') and form.errors:
            print(f"--- {form_name} Errors ---")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Field: {field} | Error: {error}")
                    messages.error(self.request, f"{form_name} - {field}: {error}")

    def _display_formset_errors(self, formset, formset_name):
        if hasattr(formset, 'errors') and formset.errors:
            print(f"--- {formset_name} Errors ---")
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            print(f"Row {i+1} | Field: {field} | Error: {error}")
                            messages.error(self.request, f"{formset_name} {i+1} - {field}: {error}")


class BaseTransactionUpdateView(TransactionMixin, mixins.HybridUpdateView):
    """Optimized base view for updating income and expense transactions"""
    model = IncomeExpense
    form_class = forms.IncomeExpenseForm
    template_name = "transactions/incomeexpense_form.html"
    inline_formset = forms.IncomeExpenseItemFormSet
    transaction_form_class = forms.TransactionForm
    
    def get_success_url(self):
        if self.transaction_type == 'income':
            return reverse_lazy('transactions:income_list')
        return reverse_lazy('transactions:expense_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_instance = self.object.transaction
        
        context['transaction_type'] = self.transaction_type
        # Pass instance to helper
        context['transaction_form'] = self._get_transaction_form(instance=transaction_instance)
        
        payment_formset_class = (forms.PaymentOptionIncomeFormSet if self.transaction_type == 'income' 
                               else forms.PaymentOptionExpenseFormSet)
        
        existing_payments = TransactionEntry.objects.filter(
            transaction=transaction_instance,
            account__under__locking_group__in=['BANK_ACCOUNT', 'CASH_ACCOUNT']
        )
        
        context['payment_formset'] = payment_formset_class(
            self.request.POST or None,
            instance=transaction_instance,
            queryset=existing_payments,
            prefix='payments',
            form_kwargs={'branch': self.get_branch(), 'transaction_type': self.transaction_type}
        )
        return context

    def _get_transaction_form(self, instance=None, prefix=None):
        return self.transaction_form_class(
            self.request.POST or None,
            self.request.FILES or None,
            instance=instance,
            prefix=prefix,
            transaction_type=self.transaction_type
        )

    def get_formset(self, custom_filters_map=None):
        return self.inline_formset(
            self.request.POST or None, 
            self.request.FILES or None, 
            instance=self.object,
            form_kwargs={'transaction_type': self.transaction_type, 'branch': self.get_branch()}
        )
    
    @transaction.atomic
    def form_valid(self, form):
        try:
            transaction_obj = self.object.transaction
            transaction_form = self._get_transaction_form(instance=transaction_obj)
            formset = self.get_formset()
            
            payment_formset_class = (forms.PaymentOptionIncomeFormSet if self.transaction_type == 'income' 
                                   else forms.PaymentOptionExpenseFormSet)
            payment_formset = payment_formset_class(
                self.request.POST,
                instance=transaction_obj,
                prefix='payments',
                form_kwargs={'branch': self.get_branch(), 'transaction_type': self.transaction_type}
            )

            # --- FIX: Call is_valid() on ALL forms/formsets first ---
            is_valid_txn = transaction_form.is_valid()
            is_valid_items = formset.is_valid() if formset else True
            is_valid_payments = payment_formset.is_valid() # This creates .cleaned_data

            if not (is_valid_txn and is_valid_items and is_valid_payments):
                 return self.form_invalid(form, transaction_form=transaction_form, formset=formset, payment_formset=payment_formset)

            # --- Now cleaned_data is safe to use ---
            income_expense_obj = form.save(commit=False)
            total_amount = transaction_form.cleaned_data.get('invoice_amount') or Decimal('0.00')

            # Logic for Simple (Non-GST) Entry
            if not income_expense_obj.is_gst:
                if total_amount <= 0:
                    messages.error(self.request, "Net amount must be greater than zero.")
                    return self.form_invalid(form, transaction_form=transaction_form, payment_formset=payment_formset)
                
                # Check if payment formset has at least one valid entry
                has_payment = any(
                    f.cleaned_data and not f.cleaned_data.get('DELETE') 
                    for f in payment_formset.forms 
                    if f.cleaned_data.get('amount') and f.cleaned_data.get('account')
                )
                
                if not has_payment:
                    messages.error(self.request, "Please select a Cash or Bank account and enter the amount.")
                    return self.form_invalid(form, transaction_form=transaction_form, payment_formset=payment_formset)

            # Proceed with saving...
            updated_transaction = transaction_form.save(commit=False)
            updated_transaction.status = "posted"
            # Ensure transaction branch is consistent with income expense branch
            if hasattr(self, 'object') and self.object and self.object.branch:
                updated_transaction.branch = self.object.branch
            else:
                updated_transaction.branch = self.get_branch()
            updated_transaction.save()
            
            income_expense_obj.transaction = updated_transaction
            # Only set branch if it's not already set by the form
            if not income_expense_obj.branch_id:
                income_expense_obj.branch = self.get_branch()  # Set branch on income/expense object
            income_expense_obj.save()
            
            if formset:
                formset.save()

            # Refresh Accounting Entries
            TransactionEntry.objects.filter(transaction=updated_transaction).delete()

            if self.transaction_type == 'income':
                create_income_accounting_entries(income_expense_obj, self.transaction_type, self.get_branch(), self.request.user)
            else:
                create_expense_accounting_entries(income_expense_obj, self.transaction_type, self.get_branch(), self.request.user)

            # Save payment entries
            create_payment_entries(payment_formset, updated_transaction, income_expense_obj, self.transaction_type, self.request.user)
            
            messages.success(self.request, f"{self.transaction_type.title()} updated successfully.")
            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            messages.error(self.request, f"Update failed: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form, transaction_form=None, formset=None, payment_formset=None):
        # Implementation of error reporting
        if transaction_form: self._display_form_errors(transaction_form, "Transaction")
        if formset: self._display_formset_errors(formset, "Items")
        if payment_formset: self._display_formset_errors(payment_formset, "Payments")
        
        return super().form_invalid(form)

    def _display_form_errors(self, form, form_name):
        return BaseTransactionCreateView._display_form_errors(self, form, form_name)

    def _display_formset_errors(self, formset, formset_name):
        return BaseTransactionCreateView._display_formset_errors(self, formset, formset_name)

    
class ContraVoucherMixin:
    
    def get_next_voucher_number(self, lookup_field="voucher_number"):
        # Assuming generate_next_voucher_number is a utility function you have imported
        return generate_next_voucher_number(
            model=Transaction,
            branch=None,  
            transaction_type='contra',
            lookup_field=lookup_field
        )
    
    def _get_transaction_form(self, instance=None, prefix=None):
        form = forms.ContraVoucherTransactionForm(
            self.request.POST or None,
            self.request.FILES or None,
            instance=instance,
            prefix=prefix,
            transaction_type='contra'
        )

        if not form.data and not instance:
            form.initial['voucher_number'] = self.get_next_voucher_number()

        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        transaction_instance = self._get_transaction_instance()
        context['transaction_form'] = self._get_transaction_form(instance=transaction_instance)
        context['transaction_type'] = 'contra'
        
        return context
    
    def _get_transaction_instance(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'transaction'):
            return self.object.transaction
        return None
    
    def _create_accounting_entries(self, contra_voucher):
        """
        Creates the Debit and Credit entries for the Contra Voucher.
        Note: We do NOT re-validate accounts here because the Form.clean() 
        has already ensured the accounts are valid Cash/Bank accounts.
        """
        transaction_obj = contra_voucher.transaction
        amount = transaction_obj.invoice_amount
        
        # Clear any existing entries for updates
        TransactionEntry.objects.filter(transaction=transaction_obj).delete()
        
        if not contra_voucher.from_account or not contra_voucher.to_account:
            raise ValidationError(
                "Both from account and to account are required for contra voucher"
            )

        # 1. DEBIT the Receiver (To Account)
        # "Debit what comes in"
        TransactionEntry.objects.create(
            transaction=transaction_obj,
            account=contra_voucher.to_account,
            debit_amount=amount,
            credit_amount=Decimal('0.00'),
            description=f"Fund transfer to {contra_voucher.to_account.name} from {contra_voucher.from_account.name} (Voucher: {transaction_obj.voucher_number})",
            creator=self.request.user
        )
        
        # 2. CREDIT the Giver (From Account)
        # "Credit what goes out"
        TransactionEntry.objects.create(
            transaction=transaction_obj,
            account=contra_voucher.from_account,
            debit_amount=Decimal('0.00'),
            credit_amount=amount,
            description=f"Fund transfer from {contra_voucher.from_account.name} to {contra_voucher.to_account.name} (Voucher: {transaction_obj.voucher_number})",
            creator=self.request.user
        )
    
    def get_success_url(self):
        return reverse_lazy("transactions:contravoucher_list")
    
    def is_popup(self):
        """Check if the request is from a popup window."""
        return 'popup' in self.request.GET or '_popup' in self.request.GET
    
    def handle_save_add_new(self):
        """Handle save and add another functionality."""
        if self.request.POST.get('save_add_new'):
            # Redirect to the same create page to add another entry
            return HttpResponseRedirect(self.create_url)
        return None
    
    
class BaseTransactionDeleteView(mixins.HybridDeleteView):
    model= Transaction

    def get_success_url(self):
        transaction=self.get_object()
        if transaction.transaction_type == 'income':
            url =reverse_lazy("transactions:income_list")
        elif transaction.transaction_type == 'expense':
            url =reverse_lazy("transactions:expense_list")
        else:
            url=None
        return url


class TransactionListView(mixins.HybridListView):
    model = Transaction
    table_class = tables.TransactionTable
    filterset_fields = { 'branch': ['exact'], 'transaction_type': ['exact'], 'status': ['exact'], 'date': ['exact'],  }
    template_name = "transactions/transaction_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Transaction List"
        context["is_transaction_list"] = True
        context['is_accounting'] = True
        context['is_transactions'] = True
        context["can_add"] = False
        return context
    

class TransactionDetailView(mixins.HybridDetailView):
    model = Transaction
    template_name = "transactions/transaction_detail.html"


class TransactionCreateView(mixins.HybridCreateView):
    model = Transaction
    form_class = forms.TransactionForm
    template_name = "transactions/transaction_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Transaction Create"
        return context


class TransactionUpdateView(mixins.HybridUpdateView):
    model = Transaction
    form_class = forms.TransactionForm
    template_name = "transactions/transaction_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Transaction Update"
        return context


class TransactionDeleteView(mixins.HybridDeleteView):
    model = Transaction


class JournalVoucherListView(TransactionMixin,mixins.HybridListView):
    template_name = 'transactions/transaction_list.html'
    model=Transaction
    table_class =tables.JournalVoucherTable
    filterset_fields = {"date": ['range']}
    transaction_type="journal_voucher"
    title="Journal Vouchers"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['btn_sub_groups'] =None
        context["title"] = "Journal Vouchers"
        context['can_add'] = True
        context['new_link'] = reverse_lazy('transactions:journalvoucher_create')
        return context

    def get_queryset(self):
        return super().get_queryset().filter(transaction_type=self.transaction_type).select_related(
            
        )
        
    
# ==================== JOURNAL VOUCHER VIEWS ====================
class JournalVoucherCreateView(TransactionMixin, mixins.HybridCreateView):
    model = Transaction
    form_class = forms.JournalVoucherForm
    inline_formset = forms.TransactionEntryFormset
    template_name = "transactions/journalvoucher_form.html"
    title = "New Journal Voucher"

    transaction_type = "journal_voucher"
    url = "transactions:journalvoucher_list"
    create_url = reverse_lazy("transactions:journalvoucher_create")

    auto_complete_formset_fields = True

    # ----------------------------
    # Voucher Number
    # ----------------------------
    def get_next_voucher_number(self, lookup_field="voucher_number"):
        # Branch will be selected in the form
        return generate_next_voucher_number(
            model=Transaction,
            branch=None,
            transaction_type=self.transaction_type,
            lookup_field=lookup_field
        )

    def get_initial(self):
        initial = super().get_initial()
        initial["voucher_number"] = self.get_next_voucher_number()
        return initial

    # ----------------------------
    # Formset
    # ----------------------------
    def get_formset(self):
        if not self.inline_formset:
            return None

        return self.inline_formset(
            self.request.POST or None,
            self.request.FILES or None,
            instance=getattr(self, "object", None),
        )

    # ----------------------------
    # Form valid
    # ----------------------------
    @transaction.atomic
    def form_valid(self, form):
        formset = self.get_formset()

        if formset and not formset.is_valid():
            return self.form_invalid(form, formset=formset)

        # Basic properties
        form.instance.transaction_type = self.transaction_type
        form.instance.creator = self.request.user
        form.instance.status = "posted"

        # Branch must come from form
        if not form.instance.branch:
            messages.error(self.request, "Branch is required for Journal Voucher.")
            return self.form_invalid(form, formset=formset)

        # Ensure unique voucher number
        voucher_number = form.instance.voucher_number
        attempts = 0
        while self._voucher_exists(voucher_number, form.instance.branch, form.instance.pk):
            attempts += 1
            if attempts >= 100:
                messages.error(self.request, "Unable to generate unique voucher number.")
                return self.form_invalid(form, formset=formset)
            voucher_number = self.get_next_voucher_number()
        form.instance.voucher_number = voucher_number

        try:
            # Save transaction
            self.object = form.save()

            # Save formset entries
            if formset:
                formset.instance = self.object
                formset.save()

            # Validate double-entry balance
            self._validate_journal_balance(self.object)

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form, formset=formset)
        except Exception as e:
            # Show actual error in debug mode or in messages
            messages.error(self.request, f"Error saving Journal Voucher: {e}")
            return self.form_invalid(form, formset=formset)

        messages.success(
            self.request,
            f"Journal Voucher {self.object.voucher_number} created successfully."
        )
        return HttpResponseRedirect(reverse_lazy(self.url))

    # ----------------------------
    # Check if voucher exists
    # ----------------------------
    def _voucher_exists(self, voucher_number, branch, exclude_pk=None):
        qs = Transaction.objects.filter(
            voucher_number=voucher_number,
            transaction_type=self.transaction_type,
            branch=branch
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()

    # ----------------------------
    # Validate journal balance
    # ----------------------------
    def _validate_journal_balance(self, transaction):
        entries = transaction.entries.all()
        if not entries.exists():
            raise ValidationError("Journal voucher must have at least one entry.")

        total_debits = sum(e.debit_amount or Decimal("0.00") for e in entries)
        total_credits = sum(e.credit_amount or Decimal("0.00") for e in entries)

        if abs(total_debits - total_credits) > Decimal("0.01"):
            raise ValidationError(
                f"Journal voucher not balanced. Debit: {total_debits}, Credit: {total_credits}"
            )

        transaction.invoice_amount = total_debits
        transaction.total_amount = total_debits
        transaction.received_amount = total_debits
        transaction.balance_amount = Decimal("0.00")
        transaction.save(update_fields=[
            "invoice_amount", "total_amount", "received_amount", "balance_amount"
        ])

    # ----------------------------
    # Form invalid
    # ----------------------------
    def form_invalid(self, form, formset=None):
        if formset is None:
            formset = self.get_formset()
        # Show errors in messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        if formset:
            for i, f in enumerate(formset.forms):
                for field, errors in f.errors.items():
                    for error in errors:
                        messages.error(self.request, f"Row {i+1} - {field}: {error}")
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    # ----------------------------
    # Context
    # ----------------------------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["btn_sub_groups"] = None
        context["title"] = "New Journal Voucher"
        return context

    def get_success_url(self):
        return reverse_lazy(self.url)


class JournalVoucherUpdateView(TransactionMixin, mixins.HybridUpdateView):
    """Update view for journal voucher transactions"""
    model = Transaction
    form_class = forms.JournalVoucherForm
    inline_formset = forms.TransactionEntryFormset
    title = "Edit Journal Voucher"
    template_name = "transactions/journalvoucher_form.html"
    transaction_type = "journal_voucher"
    url = "transactions:journalvoucher_list"
    create_url = reverse_lazy('transactions:journalvoucher_create')
    auto_complete_formset_fields = True

    # ----------------------------
    # Formset
    # ----------------------------
    def get_formset(self):
        if not self.inline_formset:
            return None

        # Get the branch from the object (for GET) or POST (for validation errors)
        branch = self.object.branch
        if self.request.POST:
            branch_id = self.request.POST.get('branch')
            if branch_id:
                from branches.models import Branch # import inside or at top
                try:
                    branch = Branch.objects.get(pk=branch_id)
                except (Branch.DoesNotExist, ValueError):
                    pass

        return self.inline_formset(
            self.request.POST or None,
            self.request.FILES or None,
            instance=self.object,
            form_kwargs={
                'branch': branch
            }
        )

    # ----------------------------
    # Form valid
    # ----------------------------
    @transaction.atomic
    def form_valid(self, form):
        formset = self.get_formset()

        if formset and not formset.is_valid():
            return self.form_invalid(form, formset=formset)

        # Basic properties
        form.instance.transaction_type = self.transaction_type
        form.instance.status = "posted"

        if not form.instance.branch:
            messages.error(self.request, "Branch is required.")
            return self.form_invalid(form, formset=formset)

        # Unique voucher number check
        voucher_number = form.instance.voucher_number
        attempts = 0
        while self._voucher_exists(voucher_number, form.instance.branch, form.instance.pk):
            attempts += 1
            if attempts >= 100:
                messages.error(self.request, "Unable to generate unique voucher number.")
                return self.form_invalid(form, formset=formset)
            voucher_number = self.get_next_voucher_number()
        form.instance.voucher_number = voucher_number

        try:
            # 1. Save the main Transaction object
            self.object = form.save()

            # 2. Save the formset (Django handles deletions/updates/creates automatically)
            if formset:
                formset.instance = self.object
                formset.save()

            # 3. Validate and Update Totals
            # Calling .all() here works because we are inside a transaction.atomic block
            self._validate_journal_balance(self.object)

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form, formset=formset)
        except Exception as e:
            messages.error(self.request, f"Error updating Journal Voucher: {e}")
            return self.form_invalid(form, formset=formset)

        messages.success(self.request, f"Voucher {self.object.voucher_number} updated.")
        return HttpResponseRedirect(self.get_success_url())

    # ----------------------------
    # Check if voucher exists
    # ----------------------------
    def _voucher_exists(self, voucher_number, branch, exclude_pk=None):
        qs = Transaction.objects.filter(
            voucher_number=voucher_number,
            transaction_type=self.transaction_type,
            branch=branch
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()

    # ----------------------------
    # Validate journal balance
    # ----------------------------
    def _validate_journal_balance(self, transaction):
        entries = transaction.entries.all()
        if not entries.exists():
            raise ValidationError("Journal voucher must have at least one entry.")

        total_debits = sum(e.debit_amount or Decimal("0.00") for e in entries)
        total_credits = sum(e.credit_amount or Decimal("0.00") for e in entries)

        if abs(total_debits - total_credits) > Decimal("0.01"):
            raise ValidationError(
                f"Journal voucher not balanced. Debit: {total_debits}, Credit: {total_credits}"
            )

        transaction.invoice_amount = total_debits
        transaction.total_amount = total_debits
        transaction.received_amount = total_debits
        transaction.balance_amount = Decimal("0.00")
        transaction.save(update_fields=[
            "invoice_amount", "total_amount", "received_amount", "balance_amount"
        ])

    # ----------------------------
    # Form invalid
    # ----------------------------
    def form_invalid(self, form, formset=None):
        if formset is None:
            formset = self.get_formset()

        # ================= TERMINAL PRINTING START =================
        print("\n" + "="*50)
        print("JOURNAL VOUCHER FORM ERRORS (TERMINAL)")
        print("="*50)
        
        if form.errors:
            print(f"Main Form Errors: {form.errors.as_json()}")

        if formset:
            # Print non-form errors (e.g., errors across the whole formset)
            if formset.non_form_errors():
                print(f"Formset Non-Form Errors: {formset.non_form_errors()}")
            
            # Print individual form errors within the formset
            for i, f in enumerate(formset.forms):
                if f.errors:
                    print(f"Row {i+1} Errors: {f.errors.as_json()}")
        
        print("="*50 + "\n")
        # ================= TERMINAL PRINTING END =================

        # Keep your existing logic for UI messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        if formset:
            for i, f in enumerate(formset.forms):
                for field, errors in f.errors.items():
                    for error in errors:
                        messages.error(self.request, f"Row {i+1} - {field}: {error}")
                        
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    # ----------------------------
    # Context
    # ----------------------------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Format date for datetime-local input
        if 'form' in context and context['form'].instance and context['form'].instance.date:
            context['form'].initial['date'] = context['form'].instance.date.strftime("%Y-%m-%dT%H:%M")

        context["btn_sub_groups"] = None
        context["title"] = "Edit Journal Voucher"
        return context

    def get_success_url(self):
        return reverse_lazy(self.url)


class JournalVoucherDeleteview(BaseTransactionDeleteView):
    pass


class ContraVoucherListView(TransactionMixin, mixins.HybridListView):
    """List Contra Vouchers"""
    
    model = ContraVoucher
    table_class = tables.ContraVoucherTable
    filterset_fields = {
        'transaction__date': ['gte', 'lte'],
        'transaction__branch': ['exact'],
        'from_account': ['exact'],
        'to_account': ['exact'],
    }
    title = "Bank Deposit/Withdraw Vouchers"
    template_name = 'transactions/transaction_list.html'
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'transaction',
            'from_account',
            'to_account',
            'from_account__under',
            'to_account__under'
        )
    
    # def get_filterset_kwargs(self, filterset_class):
    #     kwargs = super().get_filterset_kwargs(filterset_class)
    #     kwargs['branch'] = self.get_branch()
    #     return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['btn_sub_groups'] = []
        context['is_contravoucher_list'] = True
        return context


class ContraVoucherDetailView(TransactionMixin, mixins.HybridDetailView):
    """Detail view for Contra Voucher"""
    
    model = ContraVoucher
    template_name = "transactions/contra_detail.html"
    permission_required = 'transactions.view_contra'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contra Voucher Details'
        context['entries'] = self.object.transaction.entries.all().select_related('account')
        return context


class ContraVoucherCreateView(ContraVoucherMixin, mixins.HybridCreateView):
    model = ContraVoucher
    form_class = forms.ContraVoucherForm
    template_name = "transactions/contra_form.html"
    title = "New Contra Voucher"
    create_url = reverse_lazy("transactions:contravoucher_create")

    # ---------------- FORM INIT ----------------
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        branch = getattr(self.request, "branch", None)

        account_qs = Account.objects.filter(
            under__locking_group__in=["CASH_ACCOUNT", "BANK_ACCOUNT"],
            is_active=True,
        )

        if branch:
            account_qs = account_qs.filter(branch=branch)

        form.fields["from_account"].queryset = account_qs
        form.fields["to_account"].queryset = account_qs

        return form

    # ---------------- FORM VALID ----------------
    @transaction.atomic
    def form_valid(self, form):
        transaction_form = None
        try:
            transaction_form = self._get_transaction_form()

            if not transaction_form.is_valid():
                return self.form_invalid(form, transaction_form)

            with transaction.atomic():
                # ---------- TRANSACTION ----------
                transaction_obj = transaction_form.save(commit=False)
                transaction_obj.transaction_type = "contra"
                transaction_obj.status = "posted"
                transaction_obj.creator = self.request.user
                voucher_number = transaction_obj.voucher_number
                attempts = 0

                while self._voucher_exists(
                    voucher_number=voucher_number,
                    branch=transaction_obj.branch,
                    exclude_pk=transaction_obj.pk,
                ):
                    attempts += 1
                    if attempts >= 10:
                        raise ValidationError(
                            "Unable to generate unique voucher number."
                        )
                    voucher_number = self.get_next_voucher_number()

                transaction_obj.voucher_number = voucher_number
                transaction_obj.save()

                # ---------- CONTRA VOUCHER ----------
                contra_voucher = form.save(commit=False)
                contra_voucher.transaction = transaction_obj
                contra_voucher.creator = self.request.user
                contra_voucher.save()
                
                # Sync amounts after saving the contra voucher
                # This ensures the transaction amounts reflect the contra voucher amount
                transaction_obj.invoice_amount = contra_voucher.amount
                transaction_obj.total_amount = contra_voucher.amount
                transaction_obj.balance_amount = Decimal('0.00')
                transaction_obj.save(update_fields=['invoice_amount', 'total_amount', 'balance_amount'])

                # ---------- ACCOUNTING ENTRIES ----------
                self._create_accounting_entries(contra_voucher)

                self.object = contra_voucher

            messages.success(
                self.request,
                f"Contra Voucher {transaction_obj.voucher_number} created successfully."
            )

            # ---------- POPUP HANDLING ----------
            if self.is_popup():
                if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({
                        "success": True,
                        "close_modal": True,
                        "refresh": True,
                    })

                return HttpResponse(
                    f'<script>opener.dismissAddAnotherPopup('
                    f'window, "{self.object.pk}", "{self.object}");</script>'
                )

            # ---------- SAVE & ADD NEW ----------
            save_add_new_response = self.handle_save_add_new()
            if save_add_new_response:
                return save_add_new_response

            return HttpResponseRedirect(self.get_success_url())

        # ---------------- VALIDATION ERROR ----------------
        except ValidationError as e:
            traceback.print_exc()
            logger.exception("ContraVoucher ValidationError")

            if hasattr(e, "message_dict"):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(self.request, f"{field}: {error}")
            else:
                messages.error(self.request, str(e))

            return self.form_invalid(form, transaction_form)

        # ---------------- SYSTEM ERROR ----------------
        except Exception:
            traceback.print_exc()
            logger.exception("ContraVoucherCreateView crashed")

            messages.error(
                self.request,
                "An unexpected error occurred. Check server logs."
            )
            return self.form_invalid(form, transaction_form)

    # ---------------- FORM INVALID ----------------
    def form_invalid(self, form, transaction_form=None):
        print("\n========== CONTRA VOUCHER FORM INVALID ==========")
        print("ContraVoucherForm errors:")
        print(form.errors.as_json())

        if transaction_form:
            print("\nTransactionForm errors:")
            print(transaction_form.errors.as_json())

        traceback.print_exc()

        self._display_form_errors(form, "Contra Voucher Form")
        if transaction_form:
            self._display_form_errors(transaction_form, "Transaction Form")

        context = self.get_context_data(form=form)
        context["transaction_form"] = transaction_form
        return self.render_to_response(context)

    # ---------------- ERROR DISPLAY ----------------
    def _display_form_errors(self, form, form_name):
        if form and form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        self.request,
                        f"{form_name} - {field}: {error}"
                    )

    # ---------------- VOUCHER CHECK ----------------
    def _voucher_exists(self, voucher_number, branch, exclude_pk=None):
        qs = Transaction.objects.filter(
            voucher_number=voucher_number,
            transaction_type="contra",
            branch=branch,
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()


class ContraVoucherUpdateView(ContraVoucherMixin, TransactionMixin, mixins.HybridUpdateView):
    model = ContraVoucher
    form_class = forms.ContraVoucherForm
    template_name = "transactions/contra_form.html"
    title = "Update Contra Voucher"
    create_url = reverse_lazy("transactions:contravoucher_create")

    # ------------------------------
    # GET FORM WITH FORMATTED DATE
    # ------------------------------
    def _get_transaction_form(self, instance=None):
        kwargs = {
            "data": self.request.POST or None,
            "files": self.request.FILES or None,
            "transaction_type": "contra",
        }

        if instance:
            initial = {}
            if instance.date:
                # Format for <input type="datetime-local">
                local_date = timezone.localtime(instance.date)
                initial["date"] = local_date.strftime("%Y-%m-%dT%H:%M")
            kwargs["instance"] = instance
            kwargs["initial"] = initial

        return forms.ContraVoucherTransactionForm(**kwargs)

    # ------------------------------
    # FORM VALID
    # ------------------------------
    @transaction.atomic
    def form_valid(self, form):
        transaction_form = self._get_transaction_form(instance=self.object.transaction)

        if not transaction_form.is_valid():
            return self.form_invalid(form, transaction_form)

        try:
            with transaction.atomic():
                transaction_instance = self.object.transaction

                # Preserve immutable fields
                original_voucher = transaction_instance.voucher_number
                original_branch = transaction_instance.branch
                original_creator = transaction_instance.creator

                # ---------- TRANSACTION ----------
                transaction_obj = transaction_form.save(commit=False)
                transaction_obj.voucher_number = original_voucher
                transaction_obj.branch = original_branch
                transaction_obj.creator = original_creator
                transaction_obj.transaction_type = "contra"
                transaction_obj.status = "posted"
                # 🔥 DO NOT TOUCH transaction_obj.date — it comes from the form now
                transaction_obj.save()

                # ---------- CONTRA VOUCHER ----------
                contra_voucher = form.save(commit=False)
                contra_voucher.transaction = transaction_obj
                contra_voucher.save()

                # ---------- SYNC AMOUNTS ----------
                transaction_obj.invoice_amount = contra_voucher.amount
                transaction_obj.total_amount = contra_voucher.amount
                transaction_obj.balance_amount = Decimal("0.00")
                transaction_obj.save(
                    update_fields=[
                        "invoice_amount",
                        "total_amount",
                        "balance_amount",
                    ]
                )

                # ---------- REBUILD ENTRIES ----------
                TransactionEntry.objects.filter(transaction=transaction_obj).delete()
                self._create_accounting_entries(contra_voucher)

                self.object = contra_voucher

            messages.success(
                self.request,
                f"Contra Voucher {transaction_obj.voucher_number} updated successfully."
            )

            # ---------- POPUP HANDLING ----------
            if self.is_popup():
                if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({
                        "success": True,
                        "close_modal": True,
                        "refresh": True,
                    })

                return HttpResponse(
                    f'<script>opener.dismissAddAnotherPopup('
                    f'window, "{self.object.pk}", "{self.object}");</script>'
                )

            save_add_new_response = self.handle_save_add_new()
            if save_add_new_response:
                return save_add_new_response

            return HttpResponseRedirect(self.get_success_url())

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form, transaction_form)

        except Exception:
            messages.error(
                self.request,
                "An unexpected error occurred while updating the voucher."
            )
            return self.form_invalid(form, transaction_form)

    # ------------------------------
    # FORM INVALID
    # ------------------------------
    def form_invalid(self, form, transaction_form=None):
        if transaction_form is None:
            transaction_form = self._get_transaction_form(instance=self.object.transaction)

        self._display_form_errors(form, "Contra Voucher Form")
        self._display_form_errors(transaction_form, "Transaction Form")

        context = self.get_context_data(form=form)
        context["transaction_form"] = transaction_form
        return self.render_to_response(context)

    # ------------------------------
    # ERROR DISPLAY
    # ------------------------------
    def _display_form_errors(self, form, form_name):
        if form and form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        self.request,
                        f"{form_name} - {field}: {error}"
                    )

    # ------------------------------
    # OBJECT SAFETY
    # ------------------------------
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.transaction:
            from django.http import Http404
            raise Http404("Associated transaction not found")
        return obj

    # ------------------------------
    # SUCCESS URL
    # ------------------------------
    def get_success_url(self):
        return reverse_lazy("transactions:contravoucher_list")


class ContraVoucherDeleteView(TransactionMixin, mixins.HybridDeleteView):
    """Delete Contra Voucher"""
    
    model = ContraVoucher
    template_name = "app/common/confirm_delete.html"
    permission_required = 'transactions.delete_contra'
    
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        with transaction.atomic():
            # Delete transaction entries
            self.object.transaction.entries.all().delete()
            # Delete transaction
            self.object.transaction.delete()
            # Contra voucher will be cascade deleted
        
        messages.success(request, "Contra voucher deleted successfully.")
        return HttpResponseRedirect(success_url)


class IncomeListView(IncomeExpenseMixin,TransactionMixin,mixins.HybridListView):
    template_name = 'transactions/transaction_list.html'
    model=IncomeExpense
    table_class=tables.IncomeExpenseTable
    filterset_class = filters.IncomeExpenseFilter
    new_link ="transactions:income_create"
    title = "Incomes"
    transaction_type ="income"
    branch_field_name="transaction__branch"

    def get_queryset(self):
        return super().get_queryset().select_related('party', 'category', 'transaction').filter(transaction__transaction_type=self.transaction_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context["new_link"] = reverse_lazy(self.new_link)
        context["title"] = self.title
        return context       


class ExpenseListview(IncomeListView):
    title="Expenses"
    new_link="transactions:expense_create"
    transaction_type="expense"


class IncomeCreateView(BaseTransactionCreateView):
    """Create view for income transactions"""
    title = "New Income"
    url = "transactions:income_list"
    transaction_type = "income"
    create_url = reverse_lazy('transactions:income_create')
    auto_complete_disable_add_fields = ["party"]
    auto_complete_add_urls = {
        'category': lambda: f"{reverse_lazy('accounting:account_create')}?account_type=income",
    }


class ExpenseCreateView(BaseTransactionCreateView):
    """Create view for expense transactions"""
    title = "New Expense"
    url = "transactions:expense_list"
    transaction_type = "expense"
    create_url = reverse_lazy('transactions:expense_create')
    auto_complete_disable_add_fields = ["party"]
    auto_complete_add_urls = {
        'category': lambda: f"{reverse_lazy('accounting:account_create')}?account_type=expense",
    }

class IncomeUpdateView(BaseTransactionUpdateView):
    """Update view for income transactions"""
    title = "Update Income"
    url = "transactions:income_list"
    transaction_type = "income"
    create_url = reverse_lazy('transactions:income_create')
    auto_complete_disable_add_fields = [ "party"]
    auto_complete_add_urls = {
        'category': lambda: f"{reverse_lazy('accounting:account_create')}?account_type=income",
    }
    
class ExpenseUpdateView(BaseTransactionUpdateView):
    """Update view for expense transactions"""
    title = "Update Expense"
    url = "transactions:expense_list"
    transaction_type = "expense"
    create_url = reverse_lazy('transactions:expense_create')
    auto_complete_disable_add_fields = [ "party"]
    auto_complete_add_urls = {
        'category': lambda: f"{reverse_lazy('accounting:account_create')}?account_type=expense",
    }


class IncomeDetailView(mixins.HybridDetailView):
    model=IncomeExpense
    # template_name="transactions/income_expense_detail.html"
    title = "Income Detail"
    url = "transactions:income_list"
    transaction_type = "income"
    create_url = reverse_lazy('transactions:income_create')

class ExpenseDetailView(mixins.HybridDetailView):
    model=IncomeExpense
    # template_name="transactions/income_expense_detail.html"
    title = "Expense Detail"
    url = "transactions:expense_list"
    transaction_type = "expense"
    create_url = reverse_lazy('transactions:expense_create')


class IncomeDeleteview(BaseTransactionDeleteView):
    permission_required="transactions.delete_income"

class ExpenseDeleteview(BaseTransactionDeleteView):
    pass


class IncomeExpenseReportView(mixins.HybridTemplateView):
    template_name = "transactions/income_expense_report.html"