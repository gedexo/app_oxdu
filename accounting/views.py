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
from branches.models import Branch

from accounting.functions import generate_account_code
from transactions .models import Transaction, TransactionEntry
import re
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import RedirectView
from transactions.models import IncomeExpense
from django.views.decorators.http import require_GET
import traceback 


@login_required
@require_GET
def ajax_get_next_group_code(request):
    branch_id = request.GET.get("branch")
    prefix = "GRP"
    default_code = f"{prefix}0001"

    if not branch_id:
        return JsonResponse({"code": default_code})

    last_group = GroupMaster.objects.filter(
        branch_id=branch_id, 
        code__startswith=prefix
    ).order_by('-code').first()

    if last_group and last_group.code:
        match = re.search(r'(\d+)', last_group.code)
        if match:
            next_num = int(match.group(1)) + 1
            new_code = f"{prefix}{next_num:04d}"
            return JsonResponse({"code": new_code})

    return JsonResponse({"code": default_code})


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

        total_income = Transaction.objects.filter(
            transaction_type='income',
            status='posted'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        total_expense = Transaction.objects.filter(
            transaction_type='expense',
            status='posted'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        net_profit = total_income - total_expense

        context["total_income"] = total_income
        context["total_expense"] = total_expense
        context["net_profit"] = net_profit

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
        
        branch = form.cleaned_data.get('branch') or self.get_branch()

        if not branch:
            form.add_error('branch', "Please select a valid branch.")
            return self.form_invalid(form)

        if not formset.is_valid():
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                # 1. Save Main Group
                self.object = form.save(commit=False)
                self.object.branch = branch 
                
                # Code Uniqueness Loop
                while GroupMaster.objects.filter(branch=branch, code=self.object.code).exists():
                    self.object.code = self._generate_group_code(branch)
                
                self.object.save()

                # === CRITICAL FIX START ===
                # We must tell the formset about the parent object we just saved
                # BEFORE calling save() on the formset.
                formset.instance = self.object
                # === CRITICAL FIX END ===

                # 2. Save subgroups
                self._save_subgroups(formset, self.object)

            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            # Print error to terminal for debugging
            import traceback
            print("\n========== SAVE ERROR ==========")
            print(f"Error: {str(e)}")
            traceback.print_exc()
            print("================================\n")
            
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
        # Now this will work because formset.instance is set
        subgroups = formset.save(commit=False)
        
        existing_codes_in_batch = set()
        
        for subgroup in subgroups:
            subgroup.parent = parent_group
            subgroup.branch = parent_group.branch
            
            if not subgroup.nature_of_group:
                subgroup.nature_of_group = parent_group.nature_of_group
            if not subgroup.main_group:
                subgroup.main_group = parent_group.main_group

            # Check logic for code uniqueness
            code_exists_in_db = False
            if subgroup.code:
                code_exists_in_db = GroupMaster.objects.filter(
                    branch=parent_group.branch, 
                    code=subgroup.code
                ).exists()

            if not subgroup.code or code_exists_in_db or subgroup.code in existing_codes_in_batch:
                new_code = self._generate_group_code(parent_group.branch)
                # Loop to ensure unique code
                while (GroupMaster.objects.filter(branch=parent_group.branch, code=new_code).exists() 
                       or new_code in existing_codes_in_batch):
                    
                    match = re.search(r'(\d+)', new_code)
                    if match:
                        num = int(match.group(1)) + 1
                        new_code = f"GRP{num:04d}"
                    else:
                        import time
                        new_code = f"GRP{int(time.time())}"
                
                subgroup.code = new_code
            
            existing_codes_in_batch.add(subgroup.code)
            subgroup.save()


class GroupMasterUpdateView(mixins.HybridUpdateView):
    model = GroupMaster
    form_class = GroupMasterForm
    template_name = "accounting/groupmaster_form.html"
    branch_filter_fields = {"parent": "branch"}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['branch'] = self.get_branch()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize formset
        if self.request.POST:
            context["formset"] = SubGroupFormSet(
                self.request.POST,
                instance=self.object,
                prefix="subgroups"
            )
        else:
            context["formset"] = SubGroupFormSet(
                instance=self.object,
                prefix="subgroups"
            )

        context.update({
            "is_accounting_master": True,
            "is_groupmaster_list": True,
            "title": f"Update Group - {self.object.name}",
        })
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        # Check validity of both
        if not form.is_valid():
            return self.form_invalid(form)

        if not formset.is_valid():
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                # 1. Save Parent (GroupMasterForm handles the disabled branch field automatically)
                self.object = form.save()
                
                # 2. Save Subgroups
                self._save_subgroups(formset, self.object)

            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            form.add_error(None, f"Transaction failed: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Your existing debug prints are fine to keep here
        print("\n========== FORM ERRORS ==========")
        print(form.errors)
        context = self.get_context_data()
        if context.get('formset'):
            print("========== FORMSET ERRORS ==========")
            print(context['formset'].errors)
            print(context['formset'].non_form_errors())
            
        return super().form_invalid(form)

    def _save_subgroups(self, formset, parent_group):
        subgroups = formset.save(commit=False)
        
        # 1. Validation Logic for duplicates
        existing_codes = set()
        # Get existing codes in DB to prevent duplicates, excluding the rows we are currently saving
        current_ids = [s.pk for s in subgroups if s.pk]
        db_codes = GroupMaster.objects.filter(
            branch=parent_group.branch
        ).exclude(pk=parent_group.pk).exclude(pk__in=current_ids).values_list('code', flat=True)
        
        existing_codes.update(db_codes)

        # 2. Save Logic
        for subgroup in subgroups:
            # Check duplicate code in current iteration
            if subgroup.code in existing_codes:
                 # Note: Ideally this validation should happen in FormSet.clean, 
                 # but manual check here works for safety.
                raise forms.ValidationError(f'Code "{subgroup.code}" already exists in this branch.')
            
            if subgroup.code:
                existing_codes.add(subgroup.code)

            # Assign Relationships
            # Note: InlineFormSet automatically sets subgroup.parent = parent_group
            # We only need to set the branch manually
            subgroup.branch = parent_group.branch
            
            if not subgroup.nature_of_group:
                subgroup.nature_of_group = parent_group.nature_of_group
            if not subgroup.main_group:
                subgroup.main_group = parent_group.main_group
            
            subgroup.save()

        # 3. Delete Objects
        for obj in formset.deleted_objects:
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
        elif isinstance(value, models.Model):  
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
        kwargs.setdefault('initial', {})
        kwargs['initial']['code'] = generate_account_code()
        return kwargs

    def form_valid(self, form):
        
        with transaction.atomic():
            
            self.object = form.save()
            
            if hasattr(self, '_handle_opening_balance_transaction'):
                self._handle_opening_balance_transaction(self.object, form.cleaned_data)
            
            self.object.save()

        # HybridCreateView usually expects a call to its parent's form_valid
        return super(mixins.HybridCreateView, self).form_valid(form)

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