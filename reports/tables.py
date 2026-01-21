from django.utils.html import format_html
from django_tables2 import columns
import django_tables2 as tables
from accounting.models import Account
from core.base import BaseTable

from transactions.models import TransactionEntry


class LedgerTable(BaseTable):
    selection = None
    action = None
    voucher_no = columns.Column(accessor='transaction.voucher_number', verbose_name='Voucher No.', orderable=False)
    transaction__transaction_type = columns.Column(verbose_name='Type', orderable=False)
    description = columns.Column(verbose_name='Particulars', orderable=False)
    debit = columns.Column(accessor='debit_amount', verbose_name='Debit', orderable=False)
    credit = columns.Column(accessor='credit_amount', verbose_name='Credit', orderable=False)
    balance = columns.Column(verbose_name='Balance', orderable=False, empty_values=())

    class Meta:
        model = TransactionEntry
        attrs = {'class': 'table table-bordered table-hover', 'thead': {'class': 'table-dark'}}
        fields = ('transaction__date', 'voucher_no', 'transaction__transaction_type', 'description', 'debit', 'credit', 'balance')
        sequence = fields
        template_name = "django_tables2/table.html"

    def __init__(self, *args, **kwargs):
        self.balance_data = kwargs.pop('balance_data', {})
        super().__init__(*args, **kwargs)

    def render_voucher_no(self, value, record):
        if record.transaction and hasattr(record.transaction, 'get_update_url'):
            try:
                url = record.transaction.get_update_url()
                return format_html('<a href="{}" class="text-primary">{}</a>', url, value)
            except:
                return value
        return value

    def render_debit(self, value):
        if value > 0:
            return format_html('<span class="text-success">₹{}</span>', format(value, '.2f'))
        return '-'

    def render_credit(self, value):
        if value > 0:
            return format_html('<span class="text-danger">₹{}</span>', format(value, '.2f'))
        return '-'

    def render_balance(self, record):
        balance = self.balance_data.get(record.pk, 0)
        formatted_value = format(abs(balance), '.2f')

        if balance >= 0:
            return format_html('<span class="text-success">₹{} Dr</span>', formatted_value)
        else:
            return format_html('<span class="text-danger">₹{} Cr</span>', formatted_value)

        
class TrialBalanceTable(tables.Table):
    """Enhanced Trial Balance Table with formatting"""
    
    account_code = tables.Column(
        accessor='code',
        verbose_name='Code',
        attrs={
            'td': {'class': 'font-monospace'},
            'th': {'class': 'w-8'}
        }
    )
    
    account_name = tables.Column(
        accessor='name',
        verbose_name='Account Name',
        attrs={
            'td': {'class': 'fw-medium'},
            'th': {'class': 'w-25'}
        }
    )
    
    account_group = tables.Column(
        accessor='under__name',
        verbose_name='Group',
        attrs={
            'td': {'class': 'text-muted small'},
            'th': {'class': 'w-15'}
        }
    )
    
    opening_debit = tables.Column(
        empty_values=(),
        verbose_name='Opening DR (₹)',
        attrs={
            'td': {'class': 'text-end'},
            'th': {'class': 'w-10 text-end'}
        }
    )
    
    opening_credit = tables.Column(
        empty_values=(),
        verbose_name='Opening CR (₹)',
        attrs={
            'td': {'class': 'text-end'},
            'th': {'class': 'w-10 text-end'}
        }
    )
    
    period_debit = tables.Column(
        empty_values=(),
        verbose_name='Period DR (₹)',
        attrs={
            'td': {'class': 'text-end'},
            'th': {'class': 'w-10 text-end'}
        }
    )
    
    period_credit = tables.Column(
        empty_values=(),
        verbose_name='Period CR (₹)',
        attrs={
            'td': {'class': 'text-end'},
            'th': {'class': 'w-10 text-end'}
        }
    )
    
    closing_debit = tables.Column(
        empty_values=(),
        verbose_name='Closing DR (₹)',
        attrs={
            'td': {'class': 'text-end'},
            'th': {'class': 'w-10 text-end'}
        }
    )
    
    closing_credit = tables.Column(
        empty_values=(),
        verbose_name='Closing CR (₹)',
        attrs={
            'td': {'class': 'text-end'},
            'th': {'class': 'w-10 text-end'}
        }
    )
    
    def render_account_name(self, record):
        """Render account name with indentation for groups"""
        indent = getattr(record, 'indent_level', 0) * 20
        is_group = getattr(record, 'is_group_total', False)
        
        name_class = 'fw-bold' if is_group else ''
        
        return format_html(
            '<span class="{}" style="padding-left: {}px;">{}</span>',
            name_class,
            indent,
            record.name
        )
    
    def render_opening_debit(self, record):
        amount = getattr(record, 'opening_debit_amount', 0)
        if amount and amount > 0:
            is_group = getattr(record, 'is_group_total', False)
            class_name = 'fw-bold text-success' if is_group else 'text-success'
            return format_html('<span class="{}">{:,.2f}</span>', class_name, amount)
        return format_html('<span class="text-muted">-</span>')
    
    def render_opening_credit(self, record):
        amount = getattr(record, 'opening_credit_amount', 0)
        if amount and amount > 0:
            is_group = getattr(record, 'is_group_total', False)
            class_name = 'fw-bold text-danger' if is_group else 'text-danger'
            return format_html('<span class="{}">{:,.2f}</span>', class_name, amount)
        return format_html('<span class="text-muted">-</span>')
    
    def render_period_debit(self, record):
        amount = getattr(record, 'period_debit_amount', 0)
        if amount and amount > 0:
            is_group = getattr(record, 'is_group_total', False)
            class_name = 'fw-bold text-success' if is_group else ''
            return format_html('<span class="{}">{:,.2f}</span>', class_name, amount)
        return format_html('<span class="text-muted">-</span>')
    
    def render_period_credit(self, record):
        amount = getattr(record, 'period_credit_amount', 0)
        if amount and amount > 0:
            is_group = getattr(record, 'is_group_total', False)
            class_name = 'fw-bold text-danger' if is_group else ''
            return format_html('<span class="{}">{:,.2f}</span>', class_name, amount)
        return format_html('<span class="text-muted">-</span>')
    
    def render_closing_debit(self, record):
        amount = getattr(record, 'closing_debit_amount', 0)
        if amount and amount > 0:
            is_group = getattr(record, 'is_group_total', False)
            class_name = 'fw-bold text-success' if is_group else 'text-success'
            return format_html('<span class="{}">{:,.2f}</span>', class_name, amount)
        return format_html('<span class="text-muted">-</span>')
    
    def render_closing_credit(self, record):
        amount = getattr(record, 'closing_credit_amount', 0)
        if amount and amount > 0:
            is_group = getattr(record, 'is_group_total', False)
            class_name = 'fw-bold text-danger' if is_group else 'text-danger'
            return format_html('<span class="{}">{:,.2f}</span>', class_name, amount)
        return format_html('<span class="text-muted">-</span>')
    
    class Meta:
        model = Account
        template_name = 'django_tables2/bootstrap4.html'
        fields = [
            'account_code', 'account_name', 'account_group',
            'opening_debit', 'opening_credit',
            'period_debit', 'period_credit',
            'closing_debit', 'closing_credit'
        ]
        attrs = {
            'class': 'table table-striped table-bordered table-hover table-sm',
            'id': 'trial-balance-table'
        }
        row_attrs = {
            'class': lambda record: 'table-warning fw-bold' if getattr(record, 'is_group_total', False) else ''
        }