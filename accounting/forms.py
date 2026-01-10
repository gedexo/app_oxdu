from core.base import BaseForm
from .models import GroupMaster, Account
from django import forms


class GroupMasterForm(forms.ModelForm):
    class Meta:
        model = GroupMaster
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        # Handle branch safely
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)

        # 1. Set the initial branch if provided
        if branch:
            self.fields['branch'].initial = branch
        
        # 2. Get the current branch from initial or instance
        current_branch = branch or (self.instance.branch if self.instance.pk else None)

        # 3. Filter parent queryset
        if current_branch:
            self.fields["parent"].queryset = GroupMaster.objects.filter(
                branch=current_branch
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
        else:
            # If no branch is known yet, queryset is empty
            self.fields["parent"].queryset = GroupMaster.objects.none()

        if 'is_active' in self.fields:
            self.fields['is_active'].required = False

    def clean(self):
        cleaned = super().clean()
        branch = cleaned.get("branch")
        parent = cleaned.get("parent")
        code = cleaned.get("code")

        if parent and branch and parent.branch != branch:
            raise forms.ValidationError(
                "Parent group must be in the same branch"
            )
        
        # Check unique_together constraint manually, excluding current instance
        if branch and code:
            existing = GroupMaster.objects.filter(branch=branch, code=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError({
                    'code': 'Group master with this Branch and Code already exists.'
                })

        return cleaned
        
    
class SubGroupForm(forms.ModelForm):
    """Form for inline subgroups"""
    
    class Meta:
        model = GroupMaster
        fields = ('code', 'name', 'nature_of_group', 'main_group', 'description')
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sub-group Name'
            }),
            'nature_of_group': forms.Select(attrs={
                'class': 'form-control'
            }),
            'main_group': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Description'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make all fields optional for empty forms
        for field in self.fields.values():
            field.required = False
        
        # Remove branch and is_active fields if they exist (shouldn't be in subgroups)
        if 'branch' in self.fields:
            del self.fields['branch']
        if 'is_active' in self.fields:
            # Set default for is_active field
            self.fields['is_active'].initial = True
            # Make not required
            self.fields['is_active'].required = False
        
        # Note: We don't delete 'parent' field here because the inline formset needs it
        # The parent validation will be handled in the view when saving
    
    def clean(self):
        cleaned_data = super().clean()
        
        # For subgroups in formset, the branch will be set by the parent group
        # The validation will be properly handled when the subgroups are saved
        # in the view where parent and branch are properly associated
        
        return cleaned_data


from django.forms.models import BaseInlineFormSet

class SubGroupFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for empty forms
        if self.instance.pk:  # Only for existing parent instances
            for form in self.forms:
                if not form.instance.pk:
                    # Set initial values based on parent instance if available
                    form.initial['nature_of_group'] = self.instance.nature_of_group
                    form.initial['main_group'] = self.instance.main_group
    
    def add_fields(self, form, index):
        """Override to set initial branch value for subgroups"""
        super().add_fields(form, index)
        # Set initial branch from parent instance
        if self.instance and self.instance.pk and hasattr(self.instance, 'branch'):
            if 'branch' in form.fields:
                form.fields['branch'].initial = self.instance.branch
        
        # Also ensure parent field is set to the main group
        if self.instance and self.instance.pk:
            if 'parent' in form.fields:
                form.fields['parent'].initial = self.instance
    
    def full_clean(self):
        """Override to set branch on all forms before validation"""
        # First, make sure all forms have the correct branch set
        if self.instance and self.instance.pk and hasattr(self.instance, 'branch'):
            for form in self.forms:
                if form.instance:
                    # Set the branch on the instance before validation
                    form.instance.branch = self.instance.branch
                    # Also set the parent on the instance
                    form.instance.parent = self.instance
        
        # Run validation after setting branch/parent
        super().full_clean()
        
        # Check for duplicate codes within the formset itself
        if any(self.errors):
            return  # Skip if there are other errors
        
        seen_codes = set()
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                code = form.cleaned_data.get('code')
                if code:
                    if code in seen_codes:
                        form.add_error('code', 'Duplicate code found in subgroups.')
                    else:
                        seen_codes.add(code)
    
    def save_new(self, form, commit=True):
        """Override to ensure proper parent assignment"""
        # The parent will be set in the view, so we don't set it here
        obj = super().save_new(form, commit=False)
        # Make sure is_active is set to True by default
        if not hasattr(obj, 'is_active') or obj.is_active is None:
            obj.is_active = True
        if commit:
            obj.save()
        return obj
    
    def save_existing(self, form, instance, commit=True):
        """Override to ensure is_active is maintained"""
        obj = super().save_existing(form, instance, commit=False)
        # Ensure is_active is properly set
        if not hasattr(obj, 'is_active') or obj.is_active is None:
            obj.is_active = True
        if commit:
            obj.save()
        return obj

# Formset Factory for Subgroups
SubGroupFormSet = forms.inlineformset_factory(
    GroupMaster,  # Parent model
    GroupMaster,  # Child model (same model for tree structure)
    form=SubGroupForm,
    formset=SubGroupFormSet,
    fk_name='parent',  # Foreign key field name
    extra=1,  # Number of empty forms to display
    can_delete=True,  # Allow deletion
    min_num=0,  # Minimum number of forms
    validate_min=False,
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