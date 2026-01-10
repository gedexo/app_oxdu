from branches.models import Branch
from django import forms
from .models import CompanyProfile

class HomeForm(forms.Form):
    branch = forms.ModelChoiceField(queryset=Branch.objects.filter(is_active=True))


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ['name', 'total_value', 'number_of_shares', 'company_hold_shares']
        widgets = {
            'total_value': forms.NumberInput(attrs={'id': 'id_total_value'}),
        }