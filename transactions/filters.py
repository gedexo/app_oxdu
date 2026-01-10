from transactions.models import Transaction, IncomeExpense
import django_filters
from django_filters import DateFromToRangeFilter
from django.utils.translation import gettext_lazy as _


class TransactionFilter(django_filters.FilterSet):
    transaction_type = django_filters.ChoiceFilter(field_name='transaction_type', choices=Transaction.TRANSACTION_TYPE_CHOICES, label='Type')
    status = django_filters.ChoiceFilter(field_name='status', choices=Transaction.STATUS_CHOICES, label='Status')
    voucher_number = django_filters.CharFilter(lookup_expr='icontains', label='Voucher #')
    date = django_filters.DateFromToRangeFilter(field_name='date', label='Date Range')
    due_date = django_filters.DateFromToRangeFilter(field_name='due_date', label='Due Date')
    reference = django_filters.CharFilter(lookup_expr='icontains', label='Reference')
    narration = django_filters.CharFilter(lookup_expr='icontains', label='Narration')
    remark = django_filters.CharFilter(lookup_expr='icontains', label='Remark')

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'status', 'voucher_number', 'date', 'due_date', 'reference', 'narration', 'remark']


class IncomeExpenseFilter(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(field_name='type', choices=IncomeExpense.INCOME_EXPENSE_CHOICES, label='Type')
    amount = django_filters.RangeFilter(label='Amount')
    date = django_filters.DateFromToRangeFilter(field_name='date', label='Date Range')
    party = django_filters.CharFilter(field_name='party__name', lookup_expr='icontains', label='Party')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains', label='Category')
    description = django_filters.CharFilter(lookup_expr='icontains', label='Description')
    reference_number = django_filters.CharFilter(lookup_expr='icontains', label='Reference #')

    class Meta:
        model = IncomeExpense
        fields = ['type', 'amount', 'date', 'party', 'category', 'description', 'reference_number']