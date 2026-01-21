import json
from django import forms
from django.core.exceptions import ValidationError
import core.choices
from decimal import Decimal
from django.db.models import Q

from .models import Transaction, TransactionEntry, IncomeExpense, IncomeExpenseItem, ContraVoucher
from accounting.models import Account, GroupMaster


class ContraVoucherTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['branch', 'date', 'voucher_number', 'reference', 'narration', 'remark', 'attachment']
        widgets = {
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control dateinput',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'voucher_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reference (optional)',
            }),
            'narration': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Narration / Description',
            }),
            'remark': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Remark (optional)',
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)
        if self.transaction_type:
            self.initial['transaction_type'] = self.transaction_type
        
        if self.instance and self.instance.date:
            self.initial['date'] = self.instance.date.strftime('%Y-%m-%dT%H:%M')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.transaction_type = self.transaction_type or 'contra'
        instance.status = 'posted'
        instance.priority = 'normal'
        instance.outstanding_type = 'DR'
        instance.is_active = True
        instance.invoice_amount = instance.total_amount or Decimal('0.00')
        instance.received_amount = Decimal('0.00')
        instance.balance_amount = Decimal('0.00')
        instance.outstanding_amount = Decimal('0.00')
        if commit:
            instance.save()
        return instance


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'
        widgets = {
            'date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'due_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'delivery_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
        }

    def __init__(self, *args, **kwargs):
        self.transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)

        if 'date' in self.fields:
            self.fields['date'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        if 'due_date' in self.fields:
            self.fields['due_date'].input_formats = ['%Y-%m-%d']
        if 'delivery_date' in self.fields:
            self.fields['delivery_date'].input_formats = ['%Y-%m-%d']

        if self.instance and self.instance.pk:
            if self.instance.date:
                self.initial['date'] = self.instance.date.strftime('%Y-%m-%dT%H:%M')
            if self.instance.due_date:
                self.initial['due_date'] = self.instance.due_date.strftime('%Y-%m-%d')
            if self.instance.delivery_date:
                self.initial['delivery_date'] = self.instance.delivery_date.strftime('%Y-%m-%d')

        if self.transaction_type:
            self.fields['transaction_type'].initial = self.transaction_type
            self.fields['transaction_type'].disabled = True

        internal_fields = ['status', 'priority', 'outstanding_type', 'is_active', 'voucher_number']
        for field_name in internal_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget.attrs.pop('required', None)

        numeric_widgets = ['received_amount', 'balance_amount', 'invoice_amount', 'total_amount']
        for field_name, field in self.fields.items():
            classes = 'form-control'
            if field_name in numeric_widgets:
                classes += ' numberinput'
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing_class} {classes}".strip()
            field.widget.attrs.pop('required', None)

    def clean(self):
        cleaned_data = super().clean()
        txn_date = cleaned_data.get('date')
        due_date = cleaned_data.get('due_date')
        if txn_date:
            compare_txn_date = txn_date.date() if hasattr(txn_date, 'date') else txn_date
            if due_date:
                if due_date < compare_txn_date:
                    cleaned_data['due_date'] = compare_txn_date
            elif compare_txn_date:
                cleaned_data['due_date'] = compare_txn_date

        if not cleaned_data.get('status'):
            cleaned_data['status'] = 'posted' if self.transaction_type in ['income', 'expense'] else 'draft'
        if not cleaned_data.get('priority'):
            cleaned_data['priority'] = 'normal'
        if not cleaned_data.get('outstanding_type'):
            cleaned_data['outstanding_type'] = 'DR'
        if cleaned_data.get('is_active') is None:
            cleaned_data['is_active'] = True
        
        return cleaned_data
        

class TransactionEntryForm(forms.ModelForm):
    class Meta:
        model = TransactionEntry
        fields = ("account", "description", "debit_amount", "credit_amount")
        widgets = {
            "account": forms.Select(attrs={"class": "form-control account-select", "placeholder": "Select Account"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Description"}),
            "debit_amount": forms.NumberInput(attrs={"class": "form-control debit-input", "placeholder": "0.00", "step": "0.01", "min": "0"}),
            "credit_amount": forms.NumberInput(attrs={"class": "form-control credit-input", "placeholder": "0.00", "step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop('branch', None)
        self.company = kwargs.pop('company', None)
        # FIXED: Pop transaction_type to prevent __init__ crash
        self.transaction_type = kwargs.pop('transaction_type', None)
        
        super().__init__(*args, **kwargs)
        if not self.branch and self.instance.pk and hasattr(self.instance, 'transaction'):
            self.branch = self.instance.transaction.branch
        self._filter_account_queryset()
        for field_name in ["account", "description", "debit_amount", "credit_amount"]:
            if field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget.attrs.pop('required', None)

    def _filter_account_queryset(self):
        if 'account' not in self.fields: return
        queryset = Account.objects.all()
        if self.branch: queryset = queryset.filter(branch=self.branch)
        elif self.company: queryset = queryset.filter(company=self.company, branch__isnull=True)
        else: queryset = queryset.none()
        self.fields['account'].queryset = queryset.select_related('under').order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        debit = cleaned_data.get('debit_amount') or Decimal('0.00')
        credit = cleaned_data.get('credit_amount') or Decimal('0.00')
        if cleaned_data.get('DELETE'): return cleaned_data
        if not account and debit == Decimal('0.00') and credit == Decimal('0.00'): return cleaned_data
        if account:
            if debit == Decimal('0.00') and credit == Decimal('0.00'):
                raise forms.ValidationError("Either debit or credit amount must be greater than zero.")
            if debit > 0 and credit > 0:
                raise forms.ValidationError("Only one of debit or credit amount can be non-zero.")
        else:
            if debit > 0 or credit > 0:
                raise forms.ValidationError("Account must be selected when entering amounts.")
        return cleaned_data

    def save(self, commit=True):
        if not self.cleaned_data.get('account'): return None
        instance = super().save(commit=False)
        instance.debit_amount = instance.debit_amount or Decimal('0.00')
        instance.credit_amount = instance.credit_amount or Decimal('0.00')
        if commit: instance.save()
        return instance


TransactionEntryFormset = forms.inlineformset_factory(
    Transaction, TransactionEntry, form=TransactionEntryForm,
    extra=0, can_delete=True, min_num=2, validate_min=True, max_num=50
)


class JournalVoucherForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ("date", "branch", "voucher_number", "reference", "narration", "attachment")
        widgets = {
            "date": forms.DateTimeInput(attrs={"class": "form-control dateinput", "type": "datetime-local"}, format='%Y-%m-%dT%H:%M'),
            "voucher_number": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "reference": forms.TextInput(attrs={"class": "form-control", "placeholder": "Reference (optional)"}),
            "narration": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Narration / Description"}),
            "attachment": forms.FileInput(attrs={"class": "form-control"}),
        }
    def __init__(self, *args, **kwargs):
        # FIXED: Pop transaction_type to prevent __init__ crash
        self.transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.date:
            self.initial['date'] = self.instance.date.strftime('%Y-%m-%dT%H:%M')

    
class IncomeExpenseForm(forms.ModelForm):
    auto_round_off = forms.BooleanField(
        required=False,
        label="Round Off",
        widget=forms.CheckboxInput(attrs={"role": "switch", "class": "form-check-input", "name": "purchase_autoroundoff"}),
        initial=False
    )

    branch = forms.ModelChoiceField(
        queryset=None,  # Will be set dynamically
        required=True,
        label="Branch",
        empty_label="Select Branch",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = IncomeExpense
        exclude = ("creator", "status", "_type", "transaction")
        readonly_fields = ["tax_amount", "taxable_amount", "cgst_amount", "sgst_amount", "igst_amount", "items_discount_total", "sub_total", "total_quantity", "round_off_amount", "invoice_amount"]
        custom_input = ("tax_amount", "taxable_amount", "items_discount_total", "sub_total", "total_quantity")

    def __init__(self, *args, **kwargs):
        # FIXED: Pop transaction_type
        self.transaction_type = kwargs.pop("transaction_type", None) 
        super().__init__(*args, **kwargs)

        # Set branch queryset
        from branches.models import Branch
        self.fields['branch'].queryset = Branch.objects.all()

        if 'is_active' in self.fields:
            self.fields['is_active'].required = False

        for field_name, field in self.fields.items():
            field.widget.attrs.pop('required', None)
            if field_name == 'auto_round_off': continue
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing_classes} form-control".strip()

        for field_name in self.Meta.readonly_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['readonly'] = True
                if field_name in self.Meta.custom_input:
                    existing_classes = self.fields[field_name].widget.attrs.get('class', '')
                    self.fields[field_name].widget.attrs['class'] = f"{existing_classes} custom-input".strip()

        if "category" in self.fields:
            if self.transaction_type == "income": 
                self.fields["category"].label = "Income Account"
                # Filter accounts to show only income accounts
                from accounting.utils import get_direct_income_group_ids, get_indirect_income_group_ids
                income_group_ids = []
                if hasattr(self, 'instance') and self.instance.branch:
                    income_group_ids.extend(get_direct_income_group_ids(self.instance.branch))
                    income_group_ids.extend(get_indirect_income_group_ids(self.instance.branch))
                
                income_accounts = Account.objects.filter(under_id__in=income_group_ids) if income_group_ids else Account.objects.none()
                if hasattr(self, 'instance') and self.instance.branch:
                    income_accounts = income_accounts.filter(branch=self.instance.branch)
                self.fields["category"].queryset = income_accounts
            elif self.transaction_type == "expense": 
                self.fields["category"].label = "Expense Account"
                # Filter accounts to show only expense accounts
                from accounting.utils import get_direct_expense_group_ids, get_indirect_expense_group_ids
                expense_group_ids = []
                if hasattr(self, 'instance') and self.instance.branch:
                    expense_group_ids.extend(get_direct_expense_group_ids(self.instance.branch))
                    expense_group_ids.extend(get_indirect_expense_group_ids(self.instance.branch))
                
                expense_accounts = Account.objects.filter(under_id__in=expense_group_ids) if expense_group_ids else Account.objects.none()
                if hasattr(self, 'instance') and self.instance.branch:
                    expense_accounts = expense_accounts.filter(branch=self.instance.branch)
                self.fields["category"].queryset = expense_accounts

        # Filter party accounts based on branch and Is Party checkbox
        if "party" in self.fields:
            # Check if is_gst (Is Party) is checked, either in initial data or instance
            is_gst_checked = False
            if hasattr(self, 'instance') and self.instance.pk:  # Existing instance
                is_gst_checked = getattr(self.instance, 'is_gst', False)
            elif 'is_gst' in self.initial:  # Initial form data
                is_gst_checked = self.initial['is_gst']
            elif 'is_gst' in (getattr(self, 'data', {}) or {}):  # Posted data
                is_gst_checked = self.data.get('is_gst', False)
            
            if is_gst_checked:
                # If is_gst is checked, show Sundry Creditors and Sundry Debtors accounts
                from accounting.utils import get_sundry_creditors_group_ids, get_sundry_debtors_group_ids
                party_group_ids = []
                if hasattr(self, 'instance') and self.instance.branch:
                    party_group_ids.extend(get_sundry_creditors_group_ids(self.instance.branch))
                    party_group_ids.extend(get_sundry_debtors_group_ids(self.instance.branch))
                
                party_accounts = Account.objects.filter(under_id__in=party_group_ids) if party_group_ids else Account.objects.none()
                if hasattr(self, 'instance') and self.instance.branch:
                    party_accounts = party_accounts.filter(branch=self.instance.branch)
            else:
                # Otherwise show CUSTOMER/SUPPLIER ledger types
                party_accounts = Account.objects.filter(ledger_type__in=['CUSTOMER', 'SUPPLIER'])
                if hasattr(self, 'instance') and self.instance.branch:
                    party_accounts = party_accounts.filter(branch=self.instance.branch)
            # For existing instances, ensure the currently selected party remains in the queryset
            if hasattr(self, 'instance') and self.instance.pk and self.instance.party:
                # Add the current party to the queryset to prevent validation errors
                party_accounts = party_accounts | Account.objects.filter(pk=self.instance.party.pk)
            
            self.fields["party"].queryset = party_accounts

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_active') is None: cleaned_data['is_active'] = True
        
        # Handle dynamic party field validation based on selected branch
        selected_branch = cleaned_data.get('branch')
        selected_party = cleaned_data.get('party')
        is_gst = cleaned_data.get('is_gst', False)
        
        # If both branch and party are selected, validate that party is valid for the branch
        if selected_branch and selected_party:
            from accounting.utils import get_sundry_creditors_group_ids, get_sundry_debtors_group_ids
            
            # Check if the party is valid based on is_gst flag and branch
            if is_gst:
                # For GST/Party transactions, party should be Sundry Creditors/Debtors for this branch
                party_group_ids = get_sundry_creditors_group_ids(selected_branch) + get_sundry_debtors_group_ids(selected_branch)
                is_valid_party = Account.objects.filter(
                    pk=selected_party.pk,
                    under_id__in=party_group_ids,
                    branch=selected_branch
                ).exists()
            else:
                # For non-GST transactions, party should be CUSTOMER/SUPPLIER for this branch
                is_valid_party = Account.objects.filter(
                    pk=selected_party.pk,
                    ledger_type__in=['CUSTOMER', 'SUPPLIER'],
                    branch=selected_branch
                ).exists()
            
            # If the party is not valid for the selected branch and settings, raise an error
            if not is_valid_party:
                from django.core.exceptions import ValidationError
                raise ValidationError({'party': 'Selected party is not valid for the selected branch and settings.'})
        
        return cleaned_data
    
    def clean_party(self):
        party = self.cleaned_data.get('party')
        branch = self.cleaned_data.get('branch')
        is_gst = self.cleaned_data.get('is_gst', False)
        
        # If no party is selected, return as-is
        if not party or not branch:
            return party
        
        from accounting.utils import get_sundry_creditors_group_ids, get_sundry_debtors_group_ids
        
        # Validate based on the current is_gst state
        if is_gst:
            # For GST/Party transactions, party should be Sundry Creditors/Debtors for this branch
            party_group_ids = get_sundry_creditors_group_ids(branch) + get_sundry_debtors_group_ids(branch)
            is_valid = Account.objects.filter(
                pk=party.pk,
                under_id__in=party_group_ids,
                branch=branch
            ).exists()
            
            if not is_valid:
                raise ValidationError('Selected party is not a valid Sundry Debtor/Creditor for the selected branch.')
        else:
            # For non-GST transactions, party should be CUSTOMER/SUPPLIER for this branch
            is_valid = Account.objects.filter(
                pk=party.pk,
                ledger_type__in=['CUSTOMER', 'SUPPLIER'],
                branch=branch
            ).exists()
            
            if not is_valid:
                raise ValidationError('Selected party is not a valid CUSTOMER/SUPPLIER for the selected branch.')
        
        return party


class IncomeExpenseItemForm(forms.ModelForm):
    class Meta:
        model = IncomeExpenseItem
        fields = ("particular", "quantity", "unit_price", "discount_percentage", "discount_amount", "taxable_amount", "tax", "tax_amount", "line_total")
        widgets = {
            "particular": forms.TextInput(attrs={"class": "form-control particular-input border-0", "placeholder": "Enter particular"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control quantity-input border-0", "min": 1, "step": 1}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control unit-price-input border-0"}),
            "discount_percentage": forms.NumberInput(attrs={"class": "form-control discount_percentage-input border-0", "placeholder": "%"}),
            "discount_amount": forms.NumberInput(attrs={"class": "form-control discount_amount-input border-0", "placeholder": "₹"}),
            "taxable_amount": forms.NumberInput(attrs={"class": "form-control taxable-value-input readonly"}),
            "tax": forms.Select(attrs={"class": "form-control form-select tax-input border-0", "placeholder": "%"}),
            "tax_amount": forms.NumberInput(attrs={"class": "form-control tax_amount-input readonly border-0"}),
            "line_total": forms.NumberInput(attrs={"class": "form-control line_total-input readonly border-0"}),
        }

    def __init__(self, *args, **kwargs):
        # FIXED: Pop both branch and transaction_type
        self.branch = kwargs.pop('branch', None)
        self.transaction_type = kwargs.pop('transaction_type', None)
        
        super().__init__(*args, **kwargs)
        tax_queryset = self.fields["tax"].queryset
        if self.branch and hasattr(self.branch, 'company'):
            tax_queryset = tax_queryset.filter(company=self.branch.company)
        self.fields["tax"].queryset = tax_queryset
        self.fields["tax"].widget.attrs["data-options"] = json.dumps({str(tax.pk): float(tax.rate) for tax in tax_queryset})

        for field in self.fields:
            self.fields[field].required = False
            self.fields[field].widget.attrs.pop('required', None)

    def clean(self):
        cleaned_data = super().clean()
        particular = cleaned_data.get('particular')
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        line_total = cleaned_data.get('line_total')
        is_empty = (not particular and (not quantity or float(quantity or 0) == 0) and (not unit_price or float(unit_price or 0) == 0) and (not line_total or float(line_total or 0) == 0))
        if is_empty: raise forms.ValidationError("Empty form", code='empty')
        if not particular: raise forms.ValidationError({'particular': 'Particular is required'})
        return cleaned_data

    def save(self, commit=True):
        try:
            particular = self.cleaned_data.get("particular")
            if not particular: return None
            instance = super().save(commit=False)
            instance.quantity = self.cleaned_data.get('quantity') or 1
            instance.unit_price = self.cleaned_data.get('unit_price') or 0
            instance.discount_percentage = self.cleaned_data.get('discount_percentage') or 0
            instance.discount_amount = self.cleaned_data.get('discount_amount') or 0
            instance.taxable_amount = self.cleaned_data.get('taxable_amount') or 0
            instance.tax_amount = self.cleaned_data.get('tax_amount') or 0
            instance.line_total = self.cleaned_data.get('line_total') or 0
            if commit: instance.save()
            return instance
        except (KeyError, AttributeError): return None
    
IncomeExpenseItemFormSet = forms.inlineformset_factory(IncomeExpense, IncomeExpenseItem, form=IncomeExpenseItemForm, extra=0, can_delete=True, can_delete_extra=True, validate_min=True, min_num=1, validate_max=False)


class PaymentEntryForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=15, 
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control payment-amount-input',
            'placeholder': 'Enter received amount...',
            'step': '0.01',
            'min': '0.01'
        }),
        error_messages={'min_value': 'Amount must be greater than 0.00'}
    )
    
    class Meta:
        model = TransactionEntry
        fields = ("account",)
        widgets = {"account": forms.Select(attrs={"class": "form-select", "data-placeholder": "Select an account..."})}

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop('branch', None)
        self.company = kwargs.pop('company', None)
        self.transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)
        self._setup_account_queryset()
        self._initialize_amount_field()
        if self.transaction_type:
            self.fields['amount'].widget.attrs['class'] += f' {self.transaction_type}-amount {self.transaction_type}-payment required-field'
            self.fields['amount'].widget.attrs['data-transaction-type'] = self.transaction_type

        for field_name in self.fields:
            self.fields[field_name].required = False
            self.fields[field_name].widget.attrs.pop('required', None)

    def _setup_account_queryset(self):
        base_filter = {'under__locking_group__in': ['BANK_ACCOUNT', 'CASH_ACCOUNT']}
        if self.branch: base_filter['branch'] = self.branch
        elif self.company: base_filter['company'] = self.company; base_filter['branch__isnull'] = True
        queryset = Account.objects.filter(**base_filter).select_related('under').order_by('name')
        self.fields['account'].queryset = queryset

    def _initialize_amount_field(self):
        if self.instance and self.instance.pk:
            if self.transaction_type == 'income': self.fields['amount'].initial = self.instance.debit_amount
            elif self.transaction_type == 'expense': self.fields['amount'].initial = self.instance.credit_amount

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        amount = cleaned_data.get('amount')
        if not account and not amount: return cleaned_data
        if not account: raise ValidationError({'account': 'Account is required'})
        if not amount: raise ValidationError({'amount': 'Amount is required'})
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        amount = self.cleaned_data.get('amount', Decimal('0.00'))
        if self.transaction_type == 'income':
            instance.debit_amount = amount
            instance.credit_amount = Decimal('0.00')
        else:
            instance.credit_amount = amount
            instance.debit_amount = Decimal('0.00')
        if commit: instance.save()
        return instance


class IncomePaymentForm(PaymentEntryForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('transaction_type', 'income')
        super().__init__(*args, **kwargs)
        self.fields['amount'].label = "Received Amount"
        self.fields['account'].label = "Received In"


class ExpensePaymentForm(PaymentEntryForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('transaction_type', 'expense')
        super().__init__(*args, **kwargs)
        self.fields['amount'].label = "Paid Amount"
        self.fields['account'].label = "Paid From"


class BasePaymentFormSet(forms.BaseInlineFormSet):
    def clean(self):
        if any(self.errors): return
        forms_with_data = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
        accounts = []
        for form in forms_with_data:
            account = form.cleaned_data.get('account')
            if account:
                if account in accounts: raise ValidationError("Each account can only be used once.")
                accounts.append(account)


PaymentOptionIncomeFormSet = forms.inlineformset_factory(Transaction, TransactionEntry, form=IncomePaymentForm, formset=BasePaymentFormSet, extra=1, can_delete=True, fk_name='transaction')
PaymentOptionExpenseFormSet = forms.inlineformset_factory(Transaction, TransactionEntry, form=ExpensePaymentForm, formset=BasePaymentFormSet, extra=1, can_delete=True, fk_name='transaction')


class ContraVoucherForm(forms.ModelForm):
    from_account = forms.ModelChoiceField(queryset=Account.objects.none(), empty_label="Select Source Account", widget=forms.Select(attrs={"class": "form-select"}))
    to_account = forms.ModelChoiceField(queryset=Account.objects.none(), empty_label="Select Destination Account", widget=forms.Select(attrs={"class": "form-select"}))
    is_denomination = forms.BooleanField(required=False, label="Denomination", widget=forms.CheckboxInput(attrs={"role": "switch", "class": "form-check-input"}), initial=False)

    class Meta:
        model = ContraVoucher
        fields = ["from_account", "to_account", "amount", "transaction_mode", "cheque_number", "cheque_date", "bank_name", "is_denomination", "denomination_500", "denomination_200", "denomination_100", "denomination_50", "denomination_20", "denomination_10", "denomination_5", "denomination_2", "denomination_1"]

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop("branch", None)
        super().__init__(*args, **kwargs)
        account_qs = Account.objects.filter(is_active=True, under__locking_group__in=["CASH_ACCOUNT", "BANK_ACCOUNT"]).select_related("under", "branch")
        if self.branch: account_qs = account_qs.filter(branch=self.branch)
        self.fields["from_account"].queryset = account_qs
        self.fields["to_account"].queryset = account_qs
        self.fields["from_account"].label_from_instance = self.account_label
        self.fields["to_account"].label_from_instance = self.account_label
        for field in ("cheque_number", "cheque_date", "bank_name", "transaction_mode"):
            self.fields[field].required = False
            self.fields[field].widget.attrs.pop('required', None)

    def account_label(self, account):
        group = account.under.name if account.under else "No Group"
        branch = account.branch.name if account.branch else "No Branch"
        return f"{account.name} ({group}) - {branch}"

    def clean(self):
        cleaned_data = super().clean()
        from_acc = cleaned_data.get("from_account")
        to_acc = cleaned_data.get("to_account")
        amount = cleaned_data.get("amount")
        if from_acc and to_acc and from_acc == to_acc: self.add_error("to_account", "Source and destination accounts must be different.")
        if not amount or amount <= 0: self.add_error("amount", "Amount must be greater than zero.")
        return cleaned_data