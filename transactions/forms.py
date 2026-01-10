from django import forms
import core.choices
from decimal import Decimal
from django.db.models import Q

from .models import Transaction, TransactionEntry, IncomeExpense, ContraVoucher
from accounting.models import Account, GroupMaster
# Custom form for Contra Voucher Transactions

class ContraVoucherTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['branch', 'date', 'voucher_number', 'reference', 'narration', 'remark', 'attachment']
        widgets = {
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control dateinput',
                'type': 'datetime-local',
            }),
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set default values for required fields that are not in the form
        instance.transaction_type = self.transaction_type or 'contra'
        instance.status = 'posted'  # Contra vouchers are typically posted immediately
        instance.priority = 'normal'
        instance.outstanding_type = 'DR'
        instance.is_active = True
        
        # Initialize amounts to zero for now, they will be set later
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
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control dateinput',
                'type': 'datetime-local',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control dateinput',
                'type': 'date',
            }),
            'delivery_date': forms.DateInput(attrs={
                'class': 'form-control dateinput',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)

        if self.transaction_type:
            self.fields['transaction_type'].initial = self.transaction_type
            self.fields['transaction_type'].disabled = True

        # Set default values for required fields that may not be provided
        if not self.instance.pk:
            if 'status' in self.fields and not self.data.get('status'):
                self.fields['status'].initial = 'draft'
            if 'priority' in self.fields and not self.data.get('priority'):
                self.fields['priority'].initial = 'normal'
            if 'outstanding_type' in self.fields and not self.data.get('outstanding_type'):
                self.fields['outstanding_type'].initial = 'DR'
            if 'is_active' in self.fields and not self.data.get('is_active'):
                self.fields['is_active'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        
        # Set defaults if not provided
        if not cleaned_data.get('status'):
            cleaned_data['status'] = 'draft'
        if not cleaned_data.get('priority'):
            cleaned_data['priority'] = 'normal'
        if not cleaned_data.get('outstanding_type'):
            cleaned_data['outstanding_type'] = 'DR'
        if cleaned_data.get('is_active') is None:
            cleaned_data['is_active'] = True
        
        # For contra vouchers, some amounts can be set to defaults
        transaction_type = self.transaction_type or cleaned_data.get('transaction_type')
        if transaction_type == 'contra':
            # For contra vouchers, these amounts are typically derived later
            if not cleaned_data.get('invoice_amount'):
                cleaned_data['invoice_amount'] = Decimal('0.00')
            if not cleaned_data.get('received_amount'):
                cleaned_data['received_amount'] = Decimal('0.00')
            if not cleaned_data.get('balance_amount'):
                cleaned_data['balance_amount'] = Decimal('0.00')
            if not cleaned_data.get('outstanding_amount'):
                cleaned_data['outstanding_amount'] = Decimal('0.00')
            if not cleaned_data.get('total_amount'):
                cleaned_data['total_amount'] = Decimal('0.00')
        
        return cleaned_data

class TransactionEntryForm(forms.ModelForm):
    """Form for creating/editing transaction entries in journal vouchers"""
    
    class Meta:
        model = TransactionEntry
        fields = ("account", "description", "debit_amount", "credit_amount")
        widgets = {
            "account": forms.Select(attrs={
                "class": "form-control account-select",
                "placeholder": "Select Account"
            }),
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Description"
            }),
            "debit_amount": forms.NumberInput(attrs={
                "class": "form-control debit-input",
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0"
            }),
            "credit_amount": forms.NumberInput(attrs={
                "class": "form-control credit-input",
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0"
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract custom kwargs
        self.branch = kwargs.pop('branch', None)
        self.company = kwargs.pop('company', None)
        
        super().__init__(*args, **kwargs)
        
        # Apply scope filtering to account queryset
        self._filter_account_queryset()
        
        # Mark all fields as optional initially (for empty formset rows)
        for field in self.fields.values():
            field.required = False
        
        # Set initial values for amounts
        self.fields['debit_amount'].initial = None
        self.fields['credit_amount'].initial = None

    def _filter_account_queryset(self):
        """Filter account queryset based on user scope"""
        if not hasattr(self.fields.get('account'), 'queryset'):
            return
        
        queryset = self.fields['account'].queryset
        
        # Apply scope filtering
        if self.branch:
            # Branch-level: show accounts from this branch
            queryset = queryset.filter(branch=self.branch)
        elif self.company:
            # Company-level: show only company-level accounts (branch=None)
            queryset = queryset.filter(company=self.company, branch__isnull=True)
        
        # Order by name for better UX
        queryset = queryset.select_related('under').order_by('name')
        
        self.fields['account'].queryset = queryset

    def clean(self):
        """Validate transaction entry data"""
        cleaned_data = super().clean()
        
        account = cleaned_data.get('account')
        debit = cleaned_data.get('debit_amount') or Decimal('0.00')
        credit = cleaned_data.get('credit_amount') or Decimal('0.00')
        
        # Check if the row is empty (no account and no amounts)
        if not account and debit == Decimal('0.00') and credit == Decimal('0.00'):
            # Empty row - skip validation
            return cleaned_data
        
        # If account is provided, validate amounts
        if account:
            # Ensure at least one amount is greater than zero
            if debit == Decimal('0.00') and credit == Decimal('0.00'):
                raise forms.ValidationError(
                    "Either debit or credit amount must be greater than zero."
                )
            
            # Ensure both amounts are not set simultaneously
            if debit > 0 and credit > 0:
                raise forms.ValidationError(
                    "Only one of debit or credit amount can be non-zero."
                )
        else:
            # If no account but amounts provided
            if debit > 0 or credit > 0:
                raise forms.ValidationError(
                    "Account must be selected when entering amounts."
                )
        
        return cleaned_data

    def save(self, commit=True):
        """Save transaction entry with proper defaults"""
        # Check if this is an empty form that should not be saved
        if not self.cleaned_data.get('account'):
            return None
        
        instance = super().save(commit=False)
        
        # Ensure null values are stored as zero
        instance.debit_amount = instance.debit_amount or Decimal('0.00')
        instance.credit_amount = instance.credit_amount or Decimal('0.00')
        
        if commit:
            instance.save()
        
        return instance


# Update the formset definition
TransactionEntryFormset = forms.inlineformset_factory(
    Transaction,
    TransactionEntry,
    form=TransactionEntryForm,
    extra=0,  # Number of empty rows to show
    can_delete=True,
    can_delete_extra=True,
    min_num=2,  # Minimum 2 entries for a valid journal voucher
    validate_min=True,
    max_num=50,  # Maximum entries allowed
    validate_max=True,
)


class JournalVoucherForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            "date",
            "branch",
            "voucher_number",
            "reference",
            "narration",
            "attachment",
        )
        widgets = {
            "date": forms.DateTimeInput(attrs={
                "class": "form-control dateinput",
                "type": "datetime-local",
            }),
            "voucher_number": forms.TextInput(attrs={
                "class": "form-control",
                "readonly": True,
            }),
            "reference": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Reference (optional)",
            }),
            "narration": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Narration / Description",
            }),
            "attachment": forms.FileInput(attrs={
                "class": "form-control",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


# IncomeExpense Forms
class IncomeExpenseForm(forms.ModelForm):
    """Base form for Income and Expense transactions"""
    
    class Meta:
        model = IncomeExpense
        fields = '__all__'
        exclude = ['transaction',]  # These will be managed automatically
        widgets = {
            'type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'party': forms.Select(attrs={
                'class': 'form-control',
                'title': 'Select cash or bank account for the transaction',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'title': 'Select income or expense category account',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter amount',
            }),
            'payment_method': forms.Select(choices=core.choices.PAYMENT_METHOD_CHOICES, attrs={
                'class': 'form-control',
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reference number',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of the income/expense',
            }),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control dateinput',
                'type': 'datetime-local',
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract branch from kwargs if provided
        self.branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)
        
        # Filter party and category by branch if available
        if self.branch:
            self.fields['party'].queryset = self.fields['party'].queryset.filter(branch=self.branch)
            self.fields['category'].queryset = self.fields['category'].queryset.filter(branch=self.branch)
        
        # Set initial date to current time
        from django.utils import timezone
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        party = cleaned_data.get('party')
        category = cleaned_data.get('category')
        
        # Validate that both party and category are selected
        if not party and not category:
            raise forms.ValidationError("Both cash account and category account must be selected.")
        elif not party:
            raise forms.ValidationError("Cash account (party) must be selected.")
        elif not category:
            raise forms.ValidationError("Income/Expense category account must be selected.")
        
        return cleaned_data


class IncomeCreateForm(IncomeExpenseForm):
    """Form for creating income entries"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].choices = [('income', 'Income')]
        self.fields['type'].initial = 'income'
        # Set widget to HiddenInput to prevent user from changing the type
        self.fields['type'].widget = forms.HiddenInput()


class ExpenseCreateForm(IncomeExpenseForm):
    """Form for creating expense entries"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].choices = [('expense', 'Expense')]
        self.fields['type'].initial = 'expense'
        # Set widget to HiddenInput to prevent user from changing the type
        self.fields['type'].widget = forms.HiddenInput()


class IncomeExpenseUpdateForm(IncomeExpenseForm):
    """Form for updating income/expense entries"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Don't allow changing the type after creation - hide the field
        self.fields['type'].widget = forms.HiddenInput()


class ContraVoucherForm(forms.ModelForm):

    from_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        empty_label="Select Source Account",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    to_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        empty_label="Select Destination Account",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    is_denomination = forms.BooleanField(
        required=False,
        label="Denomination",
        widget=forms.CheckboxInput(
            attrs={"role": "switch", "class": "form-check-input"}
        ),
        initial=False,
    )

    class Meta:
        model = ContraVoucher
        fields = [
            "from_account",
            "to_account",
            "amount",
            "transaction_mode",
            "cheque_number",
            "cheque_date",
            "bank_name",
            "is_denomination",
            "denomination_500",
            "denomination_200",
            "denomination_100",
            "denomination_50",
            "denomination_20",
            "denomination_10",
            "denomination_5",
            "denomination_2",
            "denomination_1",
        ]

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop("branch", None)
        super().__init__(*args, **kwargs)

        # ---------- ACCOUNT FILTER ----------
        account_qs = Account.objects.filter(
            is_active=True,
            under__locking_group__in=["CASH_ACCOUNT", "BANK_ACCOUNT"],
        ).select_related("under", "branch")

        if self.branch:
            account_qs = account_qs.filter(branch=self.branch)

        self.fields["from_account"].queryset = account_qs
        self.fields["to_account"].queryset = account_qs

        self.fields["from_account"].label_from_instance = self.account_label
        self.fields["to_account"].label_from_instance = self.account_label

        # ---------- OPTIONAL FIELDS ----------
        for field in (
            "cheque_number",
            "cheque_date",
            "bank_name",
            "transaction_mode",
        ):
            self.fields[field].required = False

    # ---------- LABEL ----------
    def account_label(self, account):
        group = account.under.name if account.under else "No Group"
        branch = account.branch.name if account.branch else "No Branch"
        return f"{account.name} ({group}) - {branch}"

    # ---------- VALIDATION ----------
    def clean(self):
        cleaned_data = super().clean()

        from_account = cleaned_data.get("from_account")
        to_account = cleaned_data.get("to_account")
        amount = cleaned_data.get("amount")
        is_denomination = cleaned_data.get("is_denomination")
        transaction_mode = cleaned_data.get("transaction_mode")

        # --- Same account protection ---
        if from_account and to_account and from_account == to_account:
            self.add_error(
                "to_account",
                "Source and destination accounts must be different."
            )

        # --- Branch protection ---
        if self.branch:
            if from_account and from_account.branch != self.branch:
                self.add_error("from_account", "Invalid branch account selected.")
            if to_account and to_account.branch != self.branch:
                self.add_error("to_account", "Invalid branch account selected.")

        # --- Amount validation ---
        if not amount or amount <= 0:
            self.add_error("amount", "Amount must be greater than zero.")

        # --- Denomination validation ---
        if is_denomination and amount:
            denominations = {
                500: cleaned_data.get("denomination_500") or 0,
                200: cleaned_data.get("denomination_200") or 0,
                100: cleaned_data.get("denomination_100") or 0,
                50: cleaned_data.get("denomination_50") or 0,
                20: cleaned_data.get("denomination_20") or 0,
                10: cleaned_data.get("denomination_10") or 0,
                5: cleaned_data.get("denomination_5") or 0,
                2: cleaned_data.get("denomination_2") or 0,
                1: cleaned_data.get("denomination_1") or 0,
            }

            total = sum(
                Decimal(note) * Decimal(count)
                for note, count in denominations.items()
            )

            if total <= 0:
                self.add_error(
                    "is_denomination",
                    "Please enter denomination values."
                )

            elif total != amount:
                self.add_error(
                    "is_denomination",
                    f"Denomination total (₹{total}) must match amount (₹{amount})."
                )

        # --- Bank transaction validation ---
        if transaction_mode and transaction_mode != "cash":
            if not cleaned_data.get("cheque_number"):
                self.add_error(
                    "cheque_number",
                    "Reference / Cheque number is required."
                )

        return cleaned_data