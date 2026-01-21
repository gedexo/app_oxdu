from accounting.models import Account, GroupMaster
from transactions.models import TransactionEntry
from django import forms

import django_filters


class LedgerFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='transaction__date', lookup_expr='gte', label='From Date')

    date_to = django_filters.DateFilter(field_name='transaction__date', lookup_expr='lte', label='To Date')

    class Meta:
        model = TransactionEntry
        fields = ['account']

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if available
        company = kwargs.pop('company', None)
        print(company)
        super().__init__(*args, **kwargs)

        # Filter account field based on branch in session
        if company:
            self.filters['account'].queryset = self.filters['account'].queryset.filter(company=company).order_by('name')
        else:
            # If no company in session, show no accounts
            self.filters['account'].queryset = Account.objects.none()


class TrialBalanceFilter(django_filters.FilterSet):
    """Enhanced filter for Trial Balance Report"""
    
    date_from = django_filters.DateFilter(
        method='filter_date_from',
        label='From Date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'DD/MM/YYYY'
        })
    )
    
    date_to = django_filters.DateFilter(
        method='filter_date_to',
        label='To Date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'DD/MM/YYYY'
        })
    )
    
    account_group = django_filters.ModelChoiceFilter(
        queryset=GroupMaster.objects.none(),
        label='Account Group',
        empty_label='All Groups',
        widget=forms.Select(attrs={'class': 'form-control'}),
        method='filter_by_group'
    )
    
    main_group = django_filters.ChoiceFilter(
        label='Report Type',
        choices=[
            ('', 'All Accounts'),
            ('balance_sheet', 'Balance Sheet Accounts'),
            ('profit_and_loss', 'P&L Accounts'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        method='filter_by_main_group'
    )
    
    nature_of_group = django_filters.ChoiceFilter(
        label='Account Nature',
        choices=[
            ('', 'All'),
            ('Assets', 'Assets'),
            ('Liabilities', 'Liabilities'),
            ('Equity', 'Equity'),
            ('Income', 'Income'),
            ('Expense', 'Expense'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        method='filter_by_nature'
    )
    
    show_zero_balance = django_filters.BooleanFilter(
        label='Show Zero Balance Accounts',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'show_zero_balance'
        }),
        method='filter_zero_balance'
    )
    
    show_grouped = django_filters.BooleanFilter(
        label='Show Grouped by Category',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'show_grouped'
        }),
        method='filter_grouped'
    )
    
    class Meta:
        model = Account
        fields = []
    
    def __init__(self, *args, **kwargs):
        # Extract scope parameters
        self.branch = kwargs.pop('branch', None)
        self.company = kwargs.pop('company', None)
        
        super().__init__(*args, **kwargs)
        
        # Build filter for GroupMaster based on scope
        group_filter = {}
        
        if self.branch:
            group_filter['branch'] = self.branch
        elif self.company:
            group_filter['company'] = self.company
            group_filter['branch__isnull'] = True
        
        # Add soft-delete filter
        if hasattr(GroupMaster, 'deleted'):
            group_filter['deleted__isnull'] = True
        
        if group_filter:
            self.filters['account_group'].queryset = GroupMaster.objects.filter(
                **group_filter
            ).order_by('name')
    
    def filter_date_from(self, queryset, name, value):
        """Date filtering is handled in the view, not here"""
        return queryset
    
    def filter_date_to(self, queryset, name, value):
        """Date filtering is handled in the view, not here"""
        return queryset
    
    def filter_by_group(self, queryset, name, value):
        """Filter accounts by group and its descendants"""
        if value:
            descendants = value.get_descendants(include_self=True)
            return queryset.filter(under__in=descendants)
        return queryset
    
    def filter_by_main_group(self, queryset, name, value):
        """Filter by main group type (balance_sheet or profit_and_loss)"""
        if value == 'balance_sheet':
            # Assets, Liabilities, Equity
            return queryset.filter(
                under__nature_of_group__in=['Assets', 'Liabilities', 'Equity']
            )
        elif value == 'profit_and_loss':
            # Income, Expense
            return queryset.filter(
                under__nature_of_group__in=['Income', 'Expense']
            )
        return queryset
    
    def filter_by_nature(self, queryset, name, value):
        """Filter by account nature (Assets, Liabilities, etc.)"""
        if value:
            return queryset.filter(under__nature_of_group=value)
        return queryset
    
    def filter_zero_balance(self, queryset, name, value):
        """Zero balance filtering is handled in the view after balance calculation"""
        return queryset
    
    def filter_grouped(self, queryset, name, value):
        """Grouping is handled in the view presentation layer"""
        return queryset