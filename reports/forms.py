from django import forms
from datetime import date

class PNLReportForm(forms.Form):
    date_from = forms.DateField(
        required=True,
        initial=date.today().replace(day=1)  # First day of current month
    )
    date_to = forms.DateField(
        required=True,
        initial=date.today()  # Today
    )
    
    def __init__(self, *args, **kwargs):
        # Import here to avoid circular imports
        from branches.models import Branch
        super().__init__(*args, **kwargs)
        
        # Add branch field with 'All' option
        all_branches = [('', 'All Branches')] + [(branch.id, branch.name) for branch in Branch.objects.all()]
        self.fields['branch_filter'] = forms.ChoiceField(
            choices=all_branches,
            required=False,
            initial='',  # Default to 'All Branches'
            widget=forms.Select(attrs={'class': 'form-control'})
        )