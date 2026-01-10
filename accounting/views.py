from django.db import transaction
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.db.models import Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, time
from decimal import Decimal
from django import forms
from core import mixins
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from .models import GroupMaster, Account
from . import tables
from .forms import GroupMasterForm, SubGroupFormSet, AccountForm, TransactionEntryFormSet

from accounting.functions import generate_account_code
from transactions .models import Transaction, TransactionEntry
import re
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import RedirectView
from transactions.models import IncomeExpense
from django.views.decorators.http import require_GET


@login_required
def get_next_group_code_ajax(request):
    branch_id = request.GET.get('branch_id')
    prefix = "GRP"
    last_group = GroupMaster.objects.filter(branch_id=branch_id, code__startswith=prefix).order_by('-code').first()
    if last_group and last_group.code:
        match = re.search(r'(\d+)', last_group.code)
        if match:
            code = f"{prefix}{(int(match.group(1)) + 1):04d}"
        else:
            code = f"{prefix}0001"
    else:
        code = f"{prefix}0001"
    return JsonResponse({'code': code})


@login_required
@require_GET
def ajax_group_master_by_branch(request):
    branch_id = request.GET.get("branch")

    if not branch_id:
        return JsonResponse([], safe=False)

    groups = GroupMaster.objects.filter(
        branch_id=branch_id,
        # is_locked=False
    ).order_by("main_group", "code")

    data = [
        {
            "id": group.id,
            "name": group.get_full_path()
        }
        for group in groups
    ]

    return JsonResponse(data, safe=False)


def get_account_type_api(request, pk):
    """
    Returns whether the account is a CASH_ACCOUNT or BANK_ACCOUNT
    based on its Group's locking_group.
    """
    account = get_object_or_404(Account, pk=pk)
    
    # We check the 'locking_group' of the parent GroupMaster
    locking_group = getattr(account.under, 'locking_group', None)
    
    return JsonResponse({
        'id': account.id,
        'name': account.name,
        'type': locking_group, # Returns 'CASH_ACCOUNT', 'BANK_ACCOUNT', etc.
        'is_cash': locking_group == 'CASH_ACCOUNT',
        'is_bank': locking_group == 'BANK_ACCOUNT'
    })


class AccountingBase(mixins.HybridTemplateView):
    template_name = "accounting/accounting_base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["is_accounting_base"] = True
        context["is_accounting"] = True

        income = IncomeExpense.objects.filter(
            type='income',
            transaction__status='posted'
        ).aggregate(total=Sum('amount'))['total'] or 0

        expense = IncomeExpense.objects.filter(
            type='expense',
            transaction__status='posted'
        ).aggregate(total=Sum('amount'))['total'] or 0

        context["total_income"] = income
        context["total_expense"] = expense
        context["net_profit"] = income - expense

        context["total_transactions"] = Transaction.objects.filter(
            status='posted'
        ).count()

        context["active_accounts"] = Account.objects.filter(
            is_locked=False
        ).count()

        return context


class GroupMasterListView(mixins.HybridListView):
    model = GroupMaster
    table_class = tables.GroupMasterTable
    filterset_fields = {
        "name": ["icontains"],
        "code": ["icontains"],
        "nature_of_group": ['exact'],
        "main_group": ['exact']
    }
    search_fields = ("name", "code", "nature_of_group", "main_group")
    template_name = "accounting/groupmaster_list.html"
    branch_filter = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_accounting"] = True
        context["is_groupmaster_list"] = True
        context["is_accounting_master"] = True
        context["can_add"] = True
        context["new_link"] = reverse_lazy("accounting:groupmaster_create")
        return context


class GroupMasterDetailView(mixins.HybridDetailView):
    model = GroupMaster
    branch_filter = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_accounting"] = True
        context["is_groupmaster_detail"] = True
        context["is_accounting_master"] = True
        context["is_groupmaster_list"] = True
        return context


class GroupMasterCreateView(mixins.HybridCreateView):
    model = GroupMaster
    form_class = GroupMasterForm
    template_name = "accounting/groupmaster_form.html"
    branch_filter_fields = {"parent": "branch"}

    def get_initial(self):
        initial = super().get_initial()
        branch = self.get_branch()
        initial['branch'] = branch
        initial['code'] = self._generate_group_code(branch)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['branch'] = self.get_branch()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['formset'] = SubGroupFormSet(self.request.POST, prefix='subgroups')
        else:
            context['formset'] = SubGroupFormSet(queryset=GroupMaster.objects.none(), prefix='subgroups')
        
        context.update({
            "is_accounting_master": True,
            "is_groupmaster_list": True,
            "title": "Create New Group",
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        # Get branch from form selection
        branch = form.cleaned_data.get('branch') or self.get_branch()

        if not branch:
            form.add_error('branch', "Please select a valid branch.")
            return self.form_invalid(form)

        if not formset.is_valid():
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                # 1. Save main group
                self.object = form.save(commit=False)
                self.object.branch = branch 
                
                # Double check uniqueness for the selected branch
                if GroupMaster.objects.filter(branch=branch, code=self.object.code).exists():
                    self.object.code = self._generate_group_code(branch)
                
                self.object.save()

                # 2. Save subgroups
                subgroups = formset.save(commit=False)
                for subgroup in subgroups:
                    subgroup.parent = self.object
                    subgroup.branch = branch
                    if not subgroup.code:
                        subgroup.code = self._generate_group_code(branch)
                    if not subgroup.nature_of_group:
                        subgroup.nature_of_group = self.object.nature_of_group
                    if not subgroup.main_group:
                        subgroup.main_group = self.object.main_group
                    subgroup.save()

            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            form.add_error(None, f"Save failed: {str(e)}")
            return self.form_invalid(form)

    def _generate_group_code(self, branch):
        prefix = "GRP"
        if not branch: return f"{prefix}0001"
        last_group = GroupMaster.objects.filter(branch=branch, code__startswith=prefix).order_by('-code').first()
        if last_group and last_group.code:
            match = re.search(r'(\d+)', last_group.code)
            if match:
                return f"{prefix}{(int(match.group(1)) + 1):04d}"
        return f"{prefix}0001"

    def _save_subgroups(self, formset, parent_group):
        subgroups = formset.save(commit=False)
        for subgroup in subgroups:
            subgroup.parent = parent_group
            subgroup.branch = parent_group.branch
            if not subgroup.code:
                subgroup.code = self._generate_group_code(parent_group.branch)
            if not subgroup.nature_of_group:
                subgroup.nature_of_group = parent_group.nature_of_group
            if not subgroup.main_group:
                subgroup.main_group = parent_group.main_group
            subgroup.save()


class GroupMasterUpdateView(mixins.HybridUpdateView):
    model = GroupMaster
    form_class = GroupMasterForm
    template_name = "accounting/groupmaster_form.html"
    branch_filter_fields = {"parent": "branch"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object

        context["formset"] = SubGroupFormSet(
            self.request.POST or None,
            instance=group,
            queryset=GroupMaster.objects.filter(parent=group),
            prefix="subgroups"
        )

        context.update({
            "is_accounting_master": True,
            "is_groupmaster_list": True,
            "title": f"Update Group - {group.name}",
        })
        return context
    
    def get_form(self, form_class=None):
        """Override to ensure branch is passed to form"""
        form = super().get_form(form_class)
        if hasattr(form, 'fields') and 'branch' in form.fields:
            # Ensure the form has the correct branch for parent filtering
            branch = self.get_branch()
            form.fields['parent'].queryset = GroupMaster.objects.filter(
                branch=branch
            ).exclude(pk=form.instance.pk if form.instance.pk else None)
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        if not form.is_valid():
            print("\nFORM INVALID IN form_valid()")
            print(form.errors.as_data())
            return self.form_invalid(form)

        if not formset.is_valid():
            print("\nFORMSET INVALID IN form_valid()")
            print(formset.errors)
            print(formset.non_form_errors())
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                group = form.save()
                self._save_subgroups(formset, group)
                self.object = group

            return super().form_valid(form)
        except forms.ValidationError as e:
            # Add the error to the form to trigger form_invalid
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        context = self.get_context_data()
        formset = context.get("formset")

        print("\n========== FORM ERRORS ==========")
        for field, errors in form.errors.items():
            print(f"{field}: {errors}")

        if form.non_field_errors():
            print("NON FIELD ERRORS:", form.non_field_errors())

        if formset:
            print("\n========== FORMSET ERRORS ==========")
            for i, f in enumerate(formset.forms):
                if f.errors:
                    print(f"\n-- SubForm {i} --")
                    for field, errors in f.errors.items():
                        print(f"{field}: {errors}")

            if formset.non_form_errors():
                print("\nFORMSET NON-FORM ERRORS:")
                print(formset.non_form_errors())

        print("=================================\n")

        return super().form_invalid(form)

    def _save_subgroups(self, formset, parent_group):
        subgroups = formset.save(commit=False)
        
        # Check for duplicate codes among the subgroups before saving
        existing_codes = set()
        for subgroup in subgroups:
            if not subgroup.code:
                continue
            
            # Check if code already exists in the same branch
            if subgroup.code in existing_codes:
                # This should not happen if formset validation worked properly
                raise forms.ValidationError(f'Duplicate code "{subgroup.code}" found in subgroups.')
            existing_codes.add(subgroup.code)
            
            # Check if code already exists in the database for this branch
            existing_in_db = GroupMaster.objects.filter(
                branch=parent_group.branch, 
                code=subgroup.code
            ).exclude(pk=subgroup.pk if subgroup.pk else None)
            
            if existing_in_db.exists():
                raise forms.ValidationError(f'Code "{subgroup.code}" already exists in this branch.')
        
        for subgroup in subgroups:
            # Set the parent relationship
            subgroup.parent = parent_group
            # Ensure branch are properly set
            subgroup.branch = parent_group.branch
            # Set default nature and main group if not provided
            if not subgroup.nature_of_group:
                subgroup.nature_of_group = parent_group.nature_of_group
            if not subgroup.main_group:
                subgroup.main_group = parent_group.main_group
            subgroup.save()

        for obj in formset.deleted_objects:
            # Check if the object has a pk before trying to delete
            if obj.pk:
                obj.delete()



class GroupMasterDeleteView(mixins.HybridDeleteView):
    model = GroupMaster


class AccountListView(mixins.HybridListView):
    model = Account
    table_class = tables.AccountTable
    filterset_fields = {
        "branch": ["exact"],
        "name": ["icontains"],
        "code": ["icontains"],
        "under": ['exact'],
        "ledger_type": ['exact']
    }
    template_name = "accounting/account_list.html"
    branch_field_name = "branch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['new_link'] = reverse_lazy("accounting:account_create")
        context['title'] = "Chart of Accounts"
        context['is_account_list'] = True
        context['is_accounting'] = True
        context["is_accounting_master"] = True
        return context

    def get_queryset(self):
        from django.db.models import Sum, F, DecimalField, Value
        from django.db.models.functions import Coalesce, Cast, Round
        
        qs = super().get_queryset().select_related('under')
        
        # Annotate with current balance calculation rounded to 2 decimal places
        qs = qs.annotate(
            total_debit=Coalesce(
                Sum('transactionentry__debit_amount'),
                Value(0),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
            total_credit=Coalesce(
                Sum('transactionentry__credit_amount'),
                Value(0),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
        ).annotate(
            balance=Cast(
                Round(F('total_debit') - F('total_credit'), 2),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        )
        
        return qs


class AccountDetailView(mixins.HybridDetailView):
    model = Account

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = str(self.object)
        context['is_account_detail'] = True
        context['is_accounting'] = True
        context["is_accounting_master"] = True
        return context

    def get_field_value(self, obj, field):
        """Helper method to safely get field values including File/Image fields"""
        value = getattr(obj, field.name)
        
        if field.get_internal_type() in ['ImageField', 'FileField']:
            return value.url if value else None
        elif hasattr(value, 'all'):  # Handle ManyToMany fields
            return [str(item) for item in value.all()]
        elif isinstance(value, models.Model):  # Handle ForeignKey
            return str(value)
        return value

    def model_to_serializable_dict(self, obj):
        """Convert model instance to JSON-serializable dictionary"""
        data = {}
        for field in obj._meta.fields:
            data[field.name] = self.get_field_value(obj, field)
        return data

    def render_to_response(self, context, **response_kwargs):
        request = self.request

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            obj = self.get_object()
            ledger_type = obj.ledger_type
            
            # Base response data
            object_data = {
                'id': obj.pk,
                'name': str(obj),
                'ledger_type': ledger_type,
            }

            # Add balance information (common for all types)
            current_balance = obj.current_balance
            object_data['outstanding_balance'] = float(current_balance)
            object_data['outstanding_balance_formatted'] = f"₹{current_balance:,.2f}"
            object_data['outstanding_balance_type'] = obj.current_balance_type

            # For GENERAL ledger, return minimal data (only balance info)
            if ledger_type == 'GENERAL':
                return JsonResponse({"success": True, "result": object_data})

            # For non-GENERAL types, add full model data
            object_data.update(self.model_to_serializable_dict(obj))
            
            # Add additional balance details
            object_data['is_overdue'] = obj.is_overdue
            object_data['available_credit'] = float(obj.available_credit) if obj.available_credit else None

            # Add addresses
            try:
                # Get default address
                default_address = obj.addresses.filter(is_default=True, is_active=True).first()
                object_data['default_address'] = default_address.pk if default_address else None
                object_data['default_address_display'] = str(default_address) if default_address else None
                object_data['state'] = default_address.state.pk if default_address and default_address.state else None
                object_data['state_display'] = str(default_address.state) if default_address and default_address.state else None
                
                # Get shipping address
                shipping_address = obj.addresses.filter(
                    address_type='SHIPPING', 
                    is_active=True
                ).first()
                object_data['shipping_address'] = shipping_address.pk if shipping_address else None
                object_data['shipping_address_display'] = str(shipping_address) if shipping_address else None
                
            except Exception as e:
                object_data['default_address'] = None
                object_data['default_address_display'] = None
                object_data['shipping_address'] = None
                object_data['shipping_address_display'] = None
                object_data['state'] = None
                object_data['state_display'] = None

            # Add type-specific data
            gst_in = None
            
            if ledger_type == 'CUSTOMER':
                try:
                    customer = obj.customer
                    customer_data = model_to_dict(customer, exclude=['photo'])
                    object_data.update(customer_data)
                    if customer.price_slab:
                        object_data['price_slab_display'] = str(customer.price_slab)
                    gst_in = customer.gstin or None
                except Customer.DoesNotExist:
                    pass
                    
            elif ledger_type == 'SUPPLIER':
                try:
                    supplier = obj.supplier
                    supplier_data = self.model_to_serializable_dict(supplier)
                    object_data.update(supplier_data)
                    object_data['supplier_type'] = str(supplier.supplier_type) if supplier.supplier_type else None
                    gst_in = getattr(supplier, 'gstin', None) or None
                except Exception:
                    pass
                    
            elif ledger_type == 'EMPLOYEE':
                try:
                    employee = obj.employee
                    employee_data = self.model_to_serializable_dict(employee)
                    object_data.update({f'employee_{k}': v for k, v in employee_data.items()})
                    object_data['user'] = str(employee.user) if employee.user else None
                except Exception:
                    pass
                    
            elif ledger_type == 'STAKE_HOLDER':
                # Add stake holder specific data if needed
                pass
            
            object_data['gst_in'] = gst_in
            
            return JsonResponse({"success": True, "result": object_data})

        return super().render_to_response(context, **response_kwargs)
    
class AccountOpeningBalanceMixin:
    """Mixin to handle opening balance transaction logic"""
    
    def _handle_opening_balance_transaction(self, account, cleaned_data):
        """Handle creation or update of opening balance transaction"""
        opening_balance = cleaned_data.get('opening_balance')
        opening_balance_date = cleaned_data.get('opening_balance_date')
        balance_type = cleaned_data.get('balance_type')
        
        # Convert to Decimal if needed
        if opening_balance is not None:
            try:
                opening_balance = Decimal(str(opening_balance))
            except (ValueError, TypeError, decimal.InvalidOperation):
                opening_balance = None
        
        # If no opening balance or zero, delete existing transaction if any
        if not opening_balance or opening_balance <= Decimal('0'):
            if account.opening_transaction:
                print(f"🗑️  Deleting opening balance transaction for {account.name}")
                account.opening_transaction.delete()
                account.opening_transaction = None
            return
        
        try:
            with transaction.atomic():
                # Check if opening transaction already exists
                if account.opening_transaction:
                    # UPDATE existing transaction
                    opening_transaction = account.opening_transaction
                    opening_transaction.invoice_amount = abs(opening_balance)
                    
                    if opening_balance_date:
                        opening_transaction.date = timezone.make_aware(
                            timezone.datetime.combine(opening_balance_date, timezone.now().time())
                        )
                    
                    opening_transaction.save()
                    print(f"✅ Transaction updated: {opening_transaction.voucher_number}")
                    
                    # Update entries
                    self._update_or_create_entries(opening_transaction, account, opening_balance, balance_type)
                    
                else:
                    # CREATE new transaction
                    print(f"🚀 Creating opening balance transaction for {account.name}")
                    
                    voucher_number = self._generate_opening_balance_voucher_number(account.branch)
                    print(f"📋 Generated voucher number: {voucher_number}")
                    
                    transaction_datetime = timezone.make_aware(
                        timezone.datetime.combine(opening_balance_date, timezone.now().time())
                    ) if opening_balance_date else timezone.now()

                    opening_transaction = Transaction.objects.create(
                        transaction_type='opening_balance',
                        status='posted',
                        voucher_number=voucher_number,
                        date=transaction_datetime,
                        reference=f"Opening Balance - {account.name}",
                        narration=f"Opening Balance for {account.name}",
                        invoice_amount=abs(opening_balance),
                        branch=account.branch,
                        creator=self.request.user if hasattr(self, 'request') else None
                    )
                    
                    print(f"✅ Transaction created: {opening_transaction.voucher_number}")
                    
                    # Create entries
                    self._create_opening_balance_entries(opening_transaction, account, opening_balance, balance_type)
                    
                    # Link transaction to account
                    account.opening_transaction = opening_transaction
                    print(f"🔗 Transaction linked to account")
                
        except Exception as e:
            print(f"❌ ERROR handling opening balance for {account.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def _update_or_create_entries(self, opening_transaction, account, opening_balance, balance_type):
        """Update existing entries or create if needed"""
        
        party_debit = abs(opening_balance) if balance_type == 'DR' else Decimal('0')
        party_credit = abs(opening_balance) if balance_type == 'CR' else Decimal('0')
        
        # Get or create party entry
        party_entry, created = TransactionEntry.objects.get_or_create(
            transaction=opening_transaction,
            account=account,
            defaults={
                'debit_amount': party_debit,
                'credit_amount': party_credit,
                'description': f"Opening Balance - {account.name}",
                'branch': account.branch,
                'creator': self.request.user if hasattr(self, 'request') else None
            }
        )
        
        if not created:
            party_entry.debit_amount = party_debit
            party_entry.credit_amount = party_credit
            party_entry.description = f"Opening Balance - {account.name}"
            party_entry.save()
            print(f"✅ Updated party entry for {account.name}")
        else:
            print(f"✅ Created party entry for {account.name}")
        
        # Get adjustment account
        opening_balance_account = self._get_opening_balance_equity_account(account.branch, balance_type)
        
        if not opening_balance_account:
            print(f"⚠️  Warning: No opening balance equity account found")
            return
        
        # Delete old contra entries if balance type changed
        existing_contra_entries = opening_transaction.entries.exclude(account=account)
        for old_contra in existing_contra_entries:
            if old_contra.account != opening_balance_account:
                print(f"🔄 Balance type changed - deleting old contra entry")
                old_contra.delete()
        
        # Get or create contra entry
        contra_entry, created = TransactionEntry.objects.get_or_create(
            transaction=opening_transaction,
            account=opening_balance_account,
            defaults={
                'debit_amount': party_credit,
                'credit_amount': party_debit,
                'description': f"Opening Balance contra - {account.name}",
                'branch': account.branch,
                'creator': self.request.user if hasattr(self, 'request') else None
            }
        )
        
        if not created:
            contra_entry.debit_amount = party_credit
            contra_entry.credit_amount = party_debit
            contra_entry.description = f"Opening Balance contra - {account.name}"
            contra_entry.save()
            print(f"✅ Updated contra entry")
        else:
            print(f"✅ Created contra entry")

    def _create_opening_balance_entries(self, opening_transaction, account, opening_balance, balance_type):
        """Create new opening balance entries"""
        
        party_debit = abs(opening_balance) if balance_type == 'DR' else Decimal('0')
        party_credit = abs(opening_balance) if balance_type == 'CR' else Decimal('0')
        
        # Create party entry
        TransactionEntry.objects.create(
            transaction=opening_transaction,
            account=account,
            debit_amount=party_debit,
            credit_amount=party_credit,
            description=f"Opening Balance - {account.name}",
            branch=account.branch,
            creator=self.request.user if hasattr(self, 'request') else None
        )
        
        # Get adjustment account
        opening_balance_account = self._get_opening_balance_equity_account(account.branch, balance_type)
        
        if opening_balance_account:
            # Create contra entry
            TransactionEntry.objects.create(
                transaction=opening_transaction,
                account=opening_balance_account,
                debit_amount=party_credit,
                credit_amount=party_debit,
                description=f"Opening Balance contra - {account.name}",
                branch=account.branch,
                creator=self.request.user if hasattr(self, 'request') else None
            )
            print(f"✅ Transaction entries created (balanced)")
        else:
            print(f"⚠️  Warning: No opening balance equity account found")

    def _get_opening_balance_equity_account(self, branch, balance_type):
        """Get the appropriate adjustment account"""
        
        locking_account = 'OPENING_BALANCE_ASSET_ADJUSTMENT' if balance_type == 'DR' else 'OPENING_BALANCE_LIABILITY_ADJUSTMENT'
        
        # Try by locking_account
        adjustment_account = Account.objects.filter(
            locking_account=locking_account,
            branch=branch
        ).first()
        
        if adjustment_account:
            return adjustment_account
        
        # Fallback: try without branch
        adjustment_account = Account.objects.filter(
            locking_account=locking_account
        ).first()
        
        if adjustment_account:
            print(f"⚠️  Using adjustment account from different branch")
            return adjustment_account
        
        print(f"❌ No adjustment account found for {locking_account}")
        return None

    def _generate_opening_balance_voucher_number(self, branch):
        """Generate unique voucher number - FIXED VERSION"""
        voucher_prefix = "OB"
        max_attempts = 100
        
        # Get the latest number from database
        latest = Transaction.objects.filter(
            branch=branch,
            transaction_type='opening_balance',
            voucher_number__startswith=voucher_prefix
        ).order_by('-voucher_number').first()
        
        if latest and latest.voucher_number:
            try:
                # Extract number from voucher (e.g., "OB0001" -> "0001")
                number_part = latest.voucher_number.replace(voucher_prefix, '')
                # Remove any non-numeric suffix (like "-1")
                number_part = re.sub(r'[^\d].*$', '', number_part)
                last_num = int(number_part) if number_part else 0
                next_num = last_num + 1
            except (ValueError, AttributeError):
                next_num = 1
        else:
            next_num = 1
        
        # Try to find unique voucher number
        for attempt in range(max_attempts):
            voucher_number = f"{voucher_prefix}{next_num:04d}"
            
            # Check if this voucher number exists
            exists = Transaction.objects.filter(
                branch=branch,
                voucher_number=voucher_number
            ).exists()
            
            if not exists:
                return voucher_number
            
            # If exists, try next number
            next_num += 1
            print(f"⚠️  Voucher {voucher_number} exists, trying next: {voucher_prefix}{next_num:04d}")
        
        # If all attempts failed, use timestamp suffix
        import time
        timestamp = int(time.time())
        voucher_number = f"{voucher_prefix}{next_num:04d}-{timestamp}"
        print(f"⚠️  Using timestamp suffix: {voucher_number}")
        
        return voucher_number


class AccountCreateView(AccountOpeningBalanceMixin, mixins.HybridCreateView):
    model = Account
    form_class = AccountForm
    template_name = "accounting/account_form.html"
    branch_filter_fields = {"under": "branch"}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        branch = self.get_branch()

        if 'initial' not in kwargs:
            kwargs['initial'] = {}

        # Auto-generate account code
        kwargs['initial']['code'] = generate_account_code(branch)

        # Pass branch so `under` loads correctly
        kwargs['initial']['branch'] = branch

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Create New Account",
            "is_accounting_master": True,
        })
        return context


class AccountUpdateView(AccountOpeningBalanceMixin, mixins.HybridUpdateView):
    model = Account
    form_class = AccountForm
    template_name = "accounting/account_form.html"
    branch_filter_fields = {"under": "branch"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_accounting_master"] = True
        context.update({
            'title': f'Update Account - {self.object.name}',
        })
        return context

    def form_valid(self, form):
        """Handle form submission"""
        with transaction.atomic():
            # Save account first
            account = form.save(commit=False)
            account.save()
            
            # Handle opening balance transaction
            self._handle_opening_balance_transaction(account, form.cleaned_data)
            
            # Save account again to update opening_transaction FK
            account.save()
            
            # Set self.object for parent class
            self.object = account
        
        return super(mixins.HybridUpdateView, self).form_valid(form)


class AccountDeleteView(mixins.HybridDeleteView):
    model = Account


class TrialBalanceView(mixins.HybridListView):
    model = Account
    template_name = "accounting/trial_balance.html"
    branch_field_name = "branch"
    table_class = tables.TrialBalanceTable
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('under').order_by('code')
        
        qs = qs.annotate(
            total_debit=Coalesce(
                Sum('transactionentry__debit_amount'),
                Decimal('0'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
            total_credit=Coalesce(
                Sum('transactionentry__credit_amount'),
                Decimal('0'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
        ).annotate(
            # Standard calculation: Debit - Credit
            balance=F('total_debit') - F('total_credit')
        )
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_reports"] = True
        
        queryset = self.get_queryset()
        
        # Calculate grand totals for the footer
        # Using the annotated 'balance' field
        total_debit = sum(acc.balance if acc.balance > 0 else 0 for acc in queryset)
        total_credit = sum(abs(acc.balance) if acc.balance < 0 else 0 for acc in queryset)
        
        context.update({
            'title': 'Trial Balance',
            'is_accounting': True,
            'is_trial_balance': True,
            'total_debit_summary': total_debit,
            'total_credit_summary': total_credit,
            'is_balanced': abs(total_debit - total_credit) < Decimal('0.01'),
            'current_date': timezone.now().date(),
        })
        
        return context


class BalanceSheetView(mixins.HybridListView):
    model = Account
    template_name = "accounting/balance_sheet.html"
    branch_field_name = "branch"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(under__main_group="balance_sheet")
            .select_related("under")
            .annotate(
                total_debit=Coalesce(
                    Sum("transactionentry__debit_amount"),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                ),
                total_credit=Coalesce(
                    Sum("transactionentry__credit_amount"),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                ),
            )
            .order_by("code")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_reports"] = True

        assets = []
        liabilities = []
        equity = []

        total_assets = Decimal("0.00")
        total_liabilities = Decimal("0.00")
        total_equity = Decimal("0.00")

        for account in self.get_queryset():
            group = account.under.nature_of_group

            if group == "Assets":
                balance = account.total_debit - account.total_credit
                if balance != 0:
                    assets.append({"account": account, "balance": balance})
                    total_assets += balance

            elif group == "Liabilities":
                balance = account.total_credit - account.total_debit
                if balance != 0:
                    liabilities.append({"account": account, "balance": balance})
                    total_liabilities += balance

            elif group == "Equity":
                balance = account.total_credit - account.total_debit
                if balance != 0:
                    equity.append({"account": account, "balance": balance})
                    total_equity += balance

        context.update({
            "title": "Balance Sheet",
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "current_date": timezone.now().date(),
            "is_accounting": True,
            "is_balance_sheet": True,
        })

        return context


class ProfitAndLossView(mixins.HybridListView):
    model = Account
    template_name = "accounting/profit_loss.html"
    branch_field_name = "branch"
    
    def get_queryset(self):
        # Get accounts for P&L (Income, Expenses)
        qs = super().get_queryset().filter(
            under__main_group='profit_and_loss'
        ).select_related('under').order_by('code')
        
        # Annotate with current balance calculation
        qs = qs.annotate(
            total_debit=Coalesce(
                Sum('transactionentry__debit_amount'),
                Decimal('0'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
            total_credit=Coalesce(
                Sum('transactionentry__credit_amount'),
                Decimal('0'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
        ).annotate(
            balance=F('total_debit') - F('total_credit')
        )
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_reports"] = True
        
        queryset = self.get_queryset()
        
        # Separate accounts by category
        income = []
        expenses = []
        
        for account in queryset:
            if account.under.nature_of_group == 'Income':
                income.append(account)
            elif account.under.nature_of_group == 'Expense':
                expenses.append(account)
        
        # Calculate totals
        total_income = sum(abs(account.current_balance) for account in income if account.current_balance < 0)  # Credit balances for income
        total_expenses = sum(abs(account.current_balance) for account in expenses if account.current_balance > 0)  # Debit balances for expenses
        
        net_profit = total_income - total_expenses
        
        context.update({
            'title': 'Profit & Loss Statement',
            'is_accounting': True,
            'is_profit_loss': True,
            'income': income,
            'expenses': expenses,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'is_profitable': net_profit >= 0,
            'current_date': timezone.now().date(),
        })
        
        return context


class LedgerReportView(mixins.BranchMixin, mixins.HybridListView):
    model = Account
    template_name = "accounting/ledger_report.html"
    
    def get_queryset(self):
        """
        Get all accounts available for this branch.
        This populates the dropdown list (object_list).
        """
        qs = super().get_queryset().select_related('under')
        
        # Ensure we only show accounts for the current branch
        branch = self.get_branch()
        if branch:
            qs = qs.filter(branch=branch)
            
        return qs.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_ledger_report"] = True
        context["is_reports"] = True
        
        # 1. Get Form Data
        account_id = self.request.GET.get('account')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        # 2. Set Dates (Default to current month if empty)
        today = timezone.now().date()
        if start_date_str:
            start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = today.replace(day=1)

        if end_date_str:
            end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = today

        # 3. Process Ledger if Account Selected
        entries = []
        opening_balance = Decimal('0.00')
        closing_balance = Decimal('0.00')
        selected_account = None

        if account_id:
            # Use the same filtering logic as get_queryset to ensure consistency
            qs = self.get_queryset()
            # We use filter().first() instead of get() to avoid crashing if ID is invalid
            selected_account = qs.filter(id=account_id).first()

            if selected_account:
                # A. Calculate Opening Balance (Sum of all transactions BEFORE start_date)
                opening_stats = TransactionEntry.objects.filter(
                    account=selected_account,
                    transaction__date__lt=start_date
                ).aggregate(
                    debit=Coalesce(Sum('debit_amount'), Decimal('0.00')),
                    credit=Coalesce(Sum('credit_amount'), Decimal('0.00'))
                )
                opening_balance = opening_stats['debit'] - opening_stats['credit']

                # B. Fetch Transactions in Range
                entries = TransactionEntry.objects.filter(
                    account=selected_account,
                    transaction__date__range=[start_date, end_date]
                ).select_related('transaction').order_by('transaction__date', 'transaction__created')

                # C. Calculate Running Balance
                running = opening_balance
                for entry in entries:
                    running = running + entry.debit_amount - entry.credit_amount
                    entry.running_balance = running
                
                closing_balance = running

        # 4. Update Context
        context.update({
            'selected_account': selected_account,
            # Pass account_id as int to helper fix template comparison
            'selected_account_id': int(account_id) if account_id else None, 
            'entries': entries,
            'opening_balance': opening_balance,
            'closing_balance': closing_balance,
            'start_date': start_date,
            'end_date': end_date,
            'title': 'Ledger Report',
        })
        
        return context


class CashFlowStatementView(mixins.BranchMixin, mixins.HybridListView):
    model = Transaction
    template_name = "accounting/cash_flow_statement.html"
    branch_field_name = "branch"
    
    # FIX: Change dictionary to a list to avoid the "dict object not callable" error
    filterset_fields = ['branch'] 

    def get_queryset(self):
        # Return posted transactions for the selected branch
        return Transaction.objects.filter(
            branch=self.get_branch(),
            status='posted'
        ).select_related('branch').order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch = self.get_branch()
        
        # 1. DATE HANDLING
        start_date_param = self.request.GET.get('start_date')
        end_date_param = self.request.GET.get('end_date')
        
        try:
            if start_date_param and end_date_param:
                start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
            else:
                # Default: Current month
                today = timezone.now().date()
                start_date = today.replace(day=1)
                end_date = today
        except ValueError:
            start_date = timezone.now().date().replace(day=1)
            end_date = timezone.now().date()

        # Convert to aware datetimes for database filtering
        start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
        end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

        # 2. IDENTIFY CASH/BANK ACCOUNTS
        # We find accounts belonging to 'Asset' that are categorized as Cash or Bank
        cash_accounts = Account.objects.filter(
            branch=branch,
            under__main_group='Asset'
        ).filter(
            Q(under__name__icontains='Cash') | 
            Q(under__name__icontains='Bank') |
            Q(name__icontains='Cash') | 
            Q(name__icontains='Bank')
        )
        cash_account_ids = set(cash_accounts.values_list('id', flat=True))

        # 3. OPENING BALANCE CALCULATION
        # Net movement of all cash accounts before the start date
        opening_data = TransactionEntry.objects.filter(
            account_id__in=cash_account_ids,
            transaction__date__lt=start_dt,
            transaction__status='posted',
            transaction__branch=branch
        ).aggregate(
            total_dr=Sum('debit_amount'),
            total_cr=Sum('credit_amount')
        )
        opening_balance = (opening_data['total_dr'] or Decimal('0')) - (opening_data['total_cr'] or Decimal('0'))

        # 4. FETCH TRANSACTIONS FOR THE PERIOD
        transactions = Transaction.objects.filter(
            branch=branch,
            status='posted',
            date__range=[start_dt, end_dt]
        ).prefetch_related('entries__account__under').order_by('date')

        # 5. CATEGORIZATION LOGIC
        categories = {
            'operating': {'items': [], 'in': Decimal('0'), 'out': Decimal('0')},
            'investing': {'items': [], 'in': Decimal('0'), 'out': Decimal('0')},
            'financing': {'items': [], 'in': Decimal('0'), 'out': Decimal('0')},
        }

        for tx in transactions:
            entries = list(tx.entries.all())
            cash_entries = [e for e in entries if e.account_id in cash_account_ids]
            other_entries = [e for e in entries if e.account_id not in cash_account_ids]

            # Skip "Contra" entries (Cash to Bank or Bank to Cash) as they don't change net cash
            if not cash_entries or not other_entries:
                continue

            for c_entry in cash_entries:
                is_inflow = c_entry.debit_amount > 0
                amount = c_entry.debit_amount if is_inflow else c_entry.credit_amount
                
                # Use the first non-cash entry to determine category
                target = other_entries[0]
                nature = target.account.under.nature_of_group # Income, Expense, Asset, Liability
                
                # Classification logic
                if nature in ['Income', 'Expense']:
                    cat = 'operating'
                elif nature == 'Asset':
                    cat = 'investing'
                elif nature in ['Liability', 'Equity']:
                    cat = 'financing'
                else:
                    cat = 'operating'

                item = {
                    'date': tx.date,
                    'description': f"{tx.get_transaction_type_display()}: {target.account.name}",
                    'amount': amount,
                    'type': 'inflow' if is_inflow else 'outflow',
                    'ref': tx.voucher_number or f"TX-{tx.id}"
                }
                
                categories[cat]['items'].append(item)
                if is_inflow:
                    categories[cat]['in'] += amount
                else:
                    categories[cat]['out'] += amount

        # 6. FINAL BALANCES
        net_op = categories['operating']['in'] - categories['operating']['out']
        net_inv = categories['investing']['in'] - categories['investing']['out']
        net_fin = categories['financing']['in'] - categories['financing']['out']
        
        net_cash_flow = net_op + net_inv + net_fin
        closing_balance = opening_balance + net_cash_flow

        context.update({
            'title': 'Cash Flow Statement',
            'is_accounting': True,
            'is_reports': True,
            
            # Activities
            'operating_activities': categories['operating']['items'],
            'investing_activities': categories['investing']['items'],
            'financing_activities': categories['financing']['items'],
            
            # Totals for summary
            'net_operating_cash_flow': net_op,
            'net_investing_cash_flow': net_inv,
            'net_financing_cash_flow': net_fin,
            
            # Global Totals
            'opening_balance': opening_balance,
            'net_cash_flow': net_cash_flow,
            'closing_balance': closing_balance,
            
            # Header info
            'start_date': start_date,
            'end_date': end_date,
            'current_date': timezone.now().date(),
        })
        return context
from django.urls import reverse
from django.views.generic import RedirectView
from transactions.models import IncomeExpense

class IncomeRedirectView(RedirectView):
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        return reverse('transactions:income_list')


class ExpenseRedirectView(RedirectView):
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        return reverse('transactions:expense_list')
