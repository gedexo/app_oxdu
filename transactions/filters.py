from transactions.models import Transaction, IncomeExpense
import django_filters
from django_filters import DateFromToRangeFilter
from django.utils.translation import gettext_lazy as _

from accounting.models import Account


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
    transaction__voucher_number = django_filters.CharFilter(lookup_expr='icontains', label='Voucher #')
    transaction__date = django_filters.DateFromToRangeFilter(label='Date Range')
    transaction__status = django_filters.ChoiceFilter(choices=Transaction.STATUS_CHOICES, label='Status')
    category = django_filters.ModelChoiceFilter(queryset=Account.objects.all(), label='Category')
    party = django_filters.ModelChoiceFilter(queryset=Account.objects.all(), label='Party')
    is_gst = django_filters.BooleanFilter(label='GST')
    auto_round_off = django_filters.BooleanFilter(label='Round Off')

    class Meta:
        model = IncomeExpense
        fields = [
            'transaction__voucher_number', 'transaction__date', 'transaction__status',
            'category', 'party', 'is_gst', 'auto_round_off',
        ]

    
class IncomeExpenseFilter(django_filters.FilterSet):
    transaction__voucher_number = django_filters.CharFilter(lookup_expr='icontains', label='Voucher #')
    transaction__date = django_filters.DateFromToRangeFilter(label='Date Range')
    transaction__status = django_filters.ChoiceFilter(choices=Transaction.STATUS_CHOICES, label='Status')
    category = django_filters.ModelChoiceFilter(queryset=Account.objects.all(), label='Category')
    party = django_filters.ModelChoiceFilter(queryset=Account.objects.all(), label='Party')
    is_gst = django_filters.BooleanFilter(label='GST')
    auto_round_off = django_filters.BooleanFilter(label='Round Off')

    class Meta:
        model = IncomeExpense
        fields = [
            'transaction__voucher_number', 'transaction__date', 'transaction__status',
            'category', 'party', 'is_gst', 'auto_round_off',
        ]