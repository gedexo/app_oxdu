from core.base import BaseForm
from .models import GroupMaster, Account
from django import forms


class GroupMasterForm(forms.ModelForm):
    class Meta:
        model = GroupMaster
        fields = "__all__"
        # We removed the 'widgets' dictionary that hid the branch
    
    def __init__(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)

        # 1. Handle Branch Field
        # If editing an existing record (instance.pk exists), make branch Read-Only
        if self.instance.pk:
            self.fields['branch'].disabled = True 
            self.fields['branch'].initial = self.instance.branch
            # When disabled=True, Django ignores POST data and uses initial/instance data
            # This fixes "This field is required" error while keeping it visible.
        elif branch:
            self.fields['branch'].initial = branch

        # 2. Filter Parent Field
        current_branch = branch or (self.instance.branch if self.instance.pk else None)
        if current_branch:
            self.fields["parent"].queryset = GroupMaster.objects.filter(
                branch=current_branch
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
        else:
            self.fields["parent"].queryset = GroupMaster.objects.none()

        # 3. Handle is_active (Fix "This field is required" for checkbox)
        if 'is_active' in self.fields:
            self.fields['is_active'].required = False

    def clean(self):
        cleaned = super().clean()
        # Note: If field is disabled, cleaned_data['branch'] will contain the initial value
        branch = cleaned.get("branch")
        parent = cleaned.get("parent")
        code = cleaned.get("code")

        if parent and branch and parent.branch != branch:
            raise forms.ValidationError("Parent group must be in the same branch")
        
        if branch and code:
            existing = GroupMaster.objects.filter(branch=branch, code=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError({'code': 'Group master with this Branch and Code already exists.'})

        return cleaned
        
    
class SubGroupForm(forms.ModelForm):
    class Meta:
        model = GroupMaster
        # Ensure 'parent' and 'branch' are excluded so they don't conflict
        exclude = ('parent', 'branch', 'created_at', 'updated_at', 'deleted_at')
        fields = ('code', 'name', 'nature_of_group', 'main_group', 'description')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sub-group Name'}),
            'nature_of_group': forms.Select(attrs={'class': 'form-control'}),
            'main_group': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


from django.forms.models import BaseInlineFormSet

class SubGroupFormSet(BaseInlineFormSet):
    def full_clean(self):
        """
        Override validation to inject the parent's branch into the 
        subgroup instances BEFORE model validation runs.
        """
        # self.instance is the Main Group (Parent)
        if self.instance and getattr(self.instance, 'branch', None):
            for form in self.forms:
                # 1. Inject Branch: Set branch on the subgroup instance
                form.instance.branch = self.instance.branch
                
                # 2. Inject Parent: Ensure parent is set (InlineFormSet does this, but safety first)
                form.instance.parent = self.instance
                
                # 3. Optional: Set defaults to ensure validation passes if fields are mandatory
                if not form.instance.nature_of_group:
                    form.instance.nature_of_group = self.instance.nature_of_group
                if not form.instance.main_group:
                    form.instance.main_group = self.instance.main_group
        
        # Now run standard validation
        super().full_clean()

    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        
        # Defensive check: Only access branch if instance exists and has it
        if self.instance and getattr(self.instance, 'pk', None) and hasattr(self.instance, 'branch'):
            obj.branch = self.instance.branch
        
        # parent is handled by BaseInlineFormSet automatically
        
        if commit:
            obj.save()
        return obj


SubGroupFormSet = forms.inlineformset_factory(
    GroupMaster,
    GroupMaster,
    form=SubGroupForm,
    formset=SubGroupFormSet, 
    fk_name='parent',
    extra=1,
    can_delete=True
)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = (
            "branch",
            "code",
            "name",
            "alias_name",
            "under",
            "ledger_type",
            "credit_limit",
            "credit_days",
            "credit_bill",
            "locking_account",
            "is_locked",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Disable `under` initially
        self.fields['under'].disabled = True
        self.fields['under'].queryset = GroupMaster.objects.none()
        self.fields['under'].help_text = "Select branch first"

        branch = None

        # Case 1: POST request
        if self.data.get('branch'):
            branch = self.data.get('branch')

        # Case 2: Editing existing instance
        elif self.instance.pk and self.instance.branch:
            branch = self.instance.branch_id

        # Case 3: Initial data (create view)
        elif self.initial.get('branch'):
            branch = self.initial.get('branch')

        # Enable and filter `under` if branch exists
        if branch:
            self.fields['under'].disabled = False
            self.fields['under'].queryset = GroupMaster.objects.filter(
                branch_id=branch
            ).order_by('main_group', 'code')
            self.fields['under'].help_text = "Select the group this account belongs to"



# Form for Journal Vouchers
from transactions.models import Transaction, TransactionEntry

class TransactionEntryForm(forms.ModelForm):
    class Meta:
        model = TransactionEntry
        fields = ('account', 'debit_amount', 'credit_amount', 'description')
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'debit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'credit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
        }
    
    def __init__(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)
        
        if branch:
            self.fields['account'].queryset = Account.objects.filter(
                branch=branch
            ).order_by('code')
        
        # Make account required
        self.fields['account'].required = True
        
        # Add help text
        self.fields['debit_amount'].help_text = "Enter amount for debit entry"
        self.fields['credit_amount'].help_text = "Enter amount for credit entry"
        
    def clean(self):
        cleaned_data = super().clean()
        debit_amount = cleaned_data.get('debit_amount', 0)
        credit_amount = cleaned_data.get('credit_amount', 0)
        
        # Ensure only one amount is entered (debit or credit)
        if debit_amount and credit_amount:
            raise forms.ValidationError("Only one of debit or credit amount can be entered")
        
        if not debit_amount and not credit_amount:
            raise forms.ValidationError("Either debit or credit amount must be entered")
        
        return cleaned_data


# Formset for Transaction Entries
TransactionEntryFormSet = forms.formset_factory(
    TransactionEntryForm,
    extra=5,
    min_num=2,
    validate_min=True,
    max_num=20,
    validate_max=True
)