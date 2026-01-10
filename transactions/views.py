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

from accounting.models import Account

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
        
        # ---------------------------------------------------------
        # CHANGE: Removed self._validate_contra_accounts() call
        # ---------------------------------------------------------
        # The form has already validated that these are valid Cash/Bank 
        # accounts (including nested sub-groups). Re-checking here with 
        # simple logic would break the hierarchy support.

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
    model = IncomeExpense
    template_name = "transactions/transaction_list.html"

    table_class = tables.IncomeExpenseTable
    filterset_class = filters.IncomeExpenseFilter

    transaction_type = "income"
    branch_field_name = "transaction__branch"

    select_related_fields = ("party", "category", "transaction")

    def get_queryset(self):
        queryset = super().get_queryset()

        return (
            queryset
            .select_related(*self.select_related_fields)
            .filter(transaction__transaction_type=self.transaction_type)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_income'] = True

        context.update({
            "title": "Incomes",
            "can_add": True,
            "new_link": reverse_lazy("transactions:income_create"),
        })

        return context


class ExpenseListView(IncomeExpenseMixin, TransactionMixin, mixins.HybridListView):
    template_name = 'transactions/transaction_list.html'
    model = IncomeExpense
    table_class = tables.IncomeExpenseTable
    filterset_class = filters.IncomeExpenseFilter
    new_link = "transactions:expense_create"
    transaction_type = "expense"
    branch_field_name = "transaction__branch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Expenses"
        context['is_expense'] = True
        context["can_add"] = True
        context["new_link"] = reverse_lazy("transactions:expense_create")
        return context

    def get_queryset(self):
        return super().get_queryset().select_related('party', 'category', 'transaction').filter(transaction__transaction_type=self.transaction_type)


class IncomeExpenseCreateView(mixins.HybridCreateView):
    model = IncomeExpense
    template_name = "transactions/income_expense_form.html"
    branch_field_name = "transaction__branch"
    
    def get_form_class(self):
        from .forms import IncomeCreateForm, ExpenseCreateForm
        # Determine type based on URL pattern first, then fallback to GET parameter
        if 'expenses' in self.request.path or self.request.GET.get('type') == 'expense':
            return ExpenseCreateForm
        else:
            return IncomeCreateForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_income_expense'] = True
        # Determine type based on URL pattern first, then fallback to GET parameter
        context['transaction_type'] = 'expense' if 'expenses' in self.request.path else self.request.GET.get('type', 'income')
        return context
    
    def form_valid(self, form):
        with transaction.atomic():

            transaction_type = (
                'expense'
                if 'expenses' in self.request.path
                else self.request.GET.get('type', 'income')
            )

            selected_branch = form.cleaned_data["branch"]

            from .models import Transaction

            transaction_obj = Transaction.objects.create(
                transaction_type=transaction_type,
                status='posted',
                date=form.cleaned_data.get('date', timezone.now()),
                narration=form.cleaned_data.get('description', ''),
                invoice_amount=form.cleaned_data.get('amount', 0),
                total_amount=form.cleaned_data.get('amount', 0),
                branch=selected_branch,   # ✅ USER SELECTED
                creator=self.request.user,
                voucher_number=self._generate_voucher_number()
            )

            income_expense = form.save(commit=False)
            income_expense.type = transaction_type
            income_expense.transaction = transaction_obj
            income_expense.branch = selected_branch
            income_expense.save()

            self._create_transaction_entries(income_expense, transaction_obj)

            self.object = income_expense

            return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect to the appropriate list page based on the type
        if self.object and self.object.type == 'expense':
            return reverse_lazy('transactions:expense_list')
        else:
            return reverse_lazy('transactions:income_list')
    
    def _generate_voucher_number(self):
        # Determine the transaction type based on URL pattern
        transaction_type = 'expense' if 'expenses' in self.request.path else self.request.GET.get('type', 'income')
        prefix = 'INC' if transaction_type == 'income' else 'EXP'
        from django.utils import timezone
        from django.db.models import Max
        from django.db.models.functions import Cast
        from django.db.models import CharField
        import re
        
        # Get the latest voucher number for this type
        latest = Transaction.objects.filter(
            transaction_type=transaction_type,
            voucher_number__startswith=prefix
        ).aggregate(Max('voucher_number'))
        
        if latest['voucher_number__max']:
            # Extract number from voucher (e.g., "INC0001" -> "0001")
            number_part = re.findall(r'\d+', latest['voucher_number__max'])
            if number_part:
                last_num = int(number_part[-1])
                next_num = last_num + 1
            else:
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:04d}"
    
    def _create_transaction_entries(self, income_expense, transaction_obj):
        """Create accounting entries for the income/expense"""
        
        # Determine accounts based on type
        if income_expense.type == 'income':
            # For income: debit the cash/bank account (party), credit the income account (category)
            debit_account = income_expense.party  # Cash/Bank account (money coming in)
            credit_account = income_expense.category  # Income account (revenue)
        else:  # expense
            # For expense: debit the expense account (category), credit the cash/bank account (party)
            debit_account = income_expense.category  # Expense account
            credit_account = income_expense.party  # Cash/Bank account (money going out)
        
        # Create the debit entry
        if debit_account:
            TransactionEntry.objects.create(
                transaction=transaction_obj,
                account=debit_account,
                debit_amount=income_expense.amount,
                credit_amount=0,
                description=income_expense.description or f"{income_expense.get_type_display()} transaction"
            )
        
        # Create the credit entry
        if credit_account:
            TransactionEntry.objects.create(
                transaction=transaction_obj,
                account=credit_account,
                debit_amount=0,
                credit_amount=income_expense.amount,
                description=income_expense.description or f"{income_expense.get_type_display()} transaction"
            )


class IncomeExpenseUpdateView(mixins.HybridUpdateView):
    model = IncomeExpense
    template_name = "transactions/income_expense_form.html"
    branch_field_name = "transaction__branch"
    
    def get_form_class(self):
        from .forms import IncomeExpenseUpdateForm
        return IncomeExpenseUpdateForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_income_expense'] = True
        context['transaction_type'] = self.object.type
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            # Update the associated transaction
            transaction_obj = self.object.transaction
            transaction_obj.date = form.cleaned_data.get('date', timezone.now())
            transaction_obj.narration = form.cleaned_data.get('description', '')
            transaction_obj.invoice_amount = form.cleaned_data.get('amount', 0)
            transaction_obj.total_amount = form.cleaned_data.get('amount', 0)
            transaction_obj.save()
            
            # Update the IncomeExpense record
            income_expense = form.save(commit=False)
            # Preserve the original type since it should not be changed after creation
            income_expense.type = self.object.type
            income_expense.save()
            
            # Update transaction entries
            self._update_transaction_entries(income_expense, transaction_obj)
            
            self.object = income_expense
            return super().form_valid(form)
    
    def _update_transaction_entries(self, income_expense, transaction_obj):
        """Update accounting entries for the income/expense"""
        from .models import TransactionEntry
        
        # Delete existing entries
        TransactionEntry.objects.filter(transaction=transaction_obj).delete()
        
        # Recreate entries based on type
        if income_expense.type == 'income':
            # For income: debit the cash/bank account (party), credit the income account (category)
            debit_account = income_expense.party  # Cash/Bank account (money coming in)
            credit_account = income_expense.category  # Income account (revenue)
        else:  # expense
            # For expense: debit the expense account (category), credit the cash/bank account (party)
            debit_account = income_expense.category  # Expense account
            credit_account = income_expense.party  # Cash/Bank account (money going out)
        
        # Create the debit entry
        if debit_account:
            TransactionEntry.objects.create(
                transaction=transaction_obj,
                account=debit_account,
                debit_amount=income_expense.amount,
                credit_amount=0,
                description=income_expense.description or f"{income_expense.get_type_display()} transaction"
            )
        
        # Create the credit entry
        if credit_account:
            TransactionEntry.objects.create(
                transaction=transaction_obj,
                account=credit_account,
                debit_amount=0,
                credit_amount=income_expense.amount,
                description=income_expense.description or f"{income_expense.get_type_display()} transaction"
            )


class IncomeExpenseDetailView(mixins.HybridDetailView):
    model = IncomeExpense
    template_name = "transactions/income_expense_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_income_expense'] = True
        return context


class IncomeExpenseDeleteView(mixins.HybridDeleteView):
    model = IncomeExpense
    
    def delete(self, request, *args, **kwargs):
        with transaction.atomic():
            income_expense = self.get_object()
            # Also delete the associated transaction
            if income_expense.transaction:
                income_expense.transaction.delete()
            return super().delete(request, *args, **kwargs)


class IncomeExpenseReportView(mixins.HybridTemplateView):
    template_name = "transactions/income_expense_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 1. Filter Handling ---
        today = timezone.now().date()
        current_year = today.year
        
        # Get params from request
        selected_month = self.request.GET.get('month')
        selected_year = self.request.GET.get('year')
        
        # Default to current year if nothing selected, or use selected values
        try:
            year_val = int(selected_year) if selected_year else current_year
        except ValueError:
            year_val = current_year

        # Determine Date Range and Grouping Strategy
        if selected_month:
            # Filter by specific Month in a Year -> Group by Day
            try:
                month_val = list(calendar.month_name).index(selected_month)
                _, last_day = calendar.monthrange(year_val, month_val)
                start_date = date(year_val, month_val, 1)
                end_date = date(year_val, month_val, last_day)
                group_by_func = TruncDay('date')
                date_format = "%d %b" # e.g., 01 Jan
                
                # Generate all days in month for chart labels
                all_periods = [
                    date(year_val, month_val, d) 
                    for d in range(1, last_day + 1)
                ]
            except ValueError:
                # Fallback if invalid month name
                start_date = date(year_val, 1, 1)
                end_date = date(year_val, 12, 31)
                group_by_func = TruncMonth('date')
                date_format = "%b %Y"
                all_periods = [date(year_val, m, 1) for m in range(1, 13)]
        else:
            # Filter by Year (or default) -> Group by Month
            start_date = date(year_val, 1, 1)
            end_date = date(year_val, 12, 31)
            group_by_func = TruncMonth('date')
            date_format = "%b %Y" # e.g., Jan 2024
            
            # Generate all months for chart labels
            all_periods = [date(year_val, m, 1) for m in range(1, 13)]

        # --- 2. Database Queries ---
        base_qs = IncomeExpense.objects.filter(
            date__date__range=[start_date, end_date],
            is_active=True
        )

        # Aggregate Totals (KPI Cards)
        totals = base_qs.aggregate(
            total_inc=Sum('amount', filter=Q(type='income')),
            total_exp=Sum('amount', filter=Q(type='expense'))
        )
        
        total_income = totals['total_inc'] or Decimal('0.00')
        total_expense = totals['total_exp'] or Decimal('0.00')
        balance = total_income - total_expense
        
        # Calculate Margin
        if total_income > 0:
            profit_margin = round((balance / total_income) * 100, 1)
        else:
            profit_margin = 0

        # --- 3. Chart Data Preparation ---
        # Get data grouped by period (Day or Month)
        income_groups = base_qs.filter(type='income')\
            .annotate(period=group_by_func)\
            .values('period')\
            .annotate(total=Sum('amount'))\
            .order_by('period')
            
        expense_groups = base_qs.filter(type='expense')\
            .annotate(period=group_by_func)\
            .values('period')\
            .annotate(total=Sum('amount'))\
            .order_by('period')

        # Convert QuerySets to Dictionaries for O(1) lookup
        # Key needs to match the iteration loop below (date object)
        inc_dict = {item['period'].date(): item['total'] for item in income_groups}
        exp_dict = {item['period'].date(): item['total'] for item in expense_groups}

        # Arrays for Chart.js
        chart_labels = []
        chart_income = []
        chart_expense = []
        table_data = []

        for period in all_periods:
            # Format Label
            label_str = period.strftime(date_format)
            chart_labels.append(label_str)
            
            # Get Values (default to 0)
            inc_val = inc_dict.get(period, Decimal('0.00'))
            exp_val = exp_dict.get(period, Decimal('0.00'))
            p_l = inc_val - exp_val
            
            chart_income.append(float(inc_val))
            chart_expense.append(float(exp_val))
            
            # Only add to table if there was activity to keep table clean
            if inc_val > 0 or exp_val > 0:
                table_data.append({
                    'get_date_display': label_str,
                    'income': inc_val,
                    'expense': exp_val,
                    'get_profit_loss': p_l
                })

        # --- 4. Context for Template ---
        context.update({
            'title': "Income & Expense Report",
            
            # Filter Data
            'months_list': list(calendar.month_name)[1:], # ['January', 'February'...]
            'available_years': range(current_year, current_year - 5, -1), # Last 5 years
            'selected_month': selected_month,
            'selected_year': int(selected_year) if selected_year else current_year,
            
            # KPI Data
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'profit_margin': profit_margin,
            
            # Chart Data (Serialized for JS)
            'labels': json.dumps(chart_labels),
            'income_data': json.dumps(chart_income),
            'expense_data': json.dumps(chart_expense),
            
            # Table Data
            'table_data': table_data,
        })
        
        return context