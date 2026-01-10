from core.base import BaseTable
from django_tables2 import columns
from django.db.models import Sum
from django.utils.html import format_html
from decimal import Decimal

from .models import Transaction, IncomeExpense, ContraVoucher

class StatusRendererMixin:
    """Mixin for consistent status rendering across all tables"""
    
    STATUS_BADGE_CLASSES = {
        'draft': 'badge bg-secondary',
        'posted': 'badge bg-success',
        'cancelled': 'badge bg-danger',
        'pending_approval': 'badge bg-warning',
        'approved': 'badge bg-info',
        'rejected': 'badge bg-danger',
    }
    
    def render_status(self, value):
        if not value:
            return format_html('<span class="badge bg-light">-</span>')
        
        badge_class = self.STATUS_BADGE_CLASSES.get(value, 'badge bg-light')
        return format_html(
            '<span class="{}">{}</span>',
            badge_class,
            value.replace('_', ' ').title()
        )

class AmountRendererMixin:
    """Mixin for consistent amount rendering across all tables"""
    
    def render_amount(self, value, color_class=""):
        """Generic amount renderer with optional color"""
        if not value:
            return "₹0.00"
        
        formatted = f"₹{value:,.2f}"
        if color_class:
            return format_html(
                '<span class="{}">{}</span>',
                color_class,
                formatted
            )
        return formatted
    
    def render_debit_amount(self, value):
        """Render debit amounts in success color"""
        return self.render_amount(value, "text-success fw-medium") if value else "-"
    
    def render_credit_amount(self, value):
        """Render credit amounts in danger color"""
        return self.render_amount(value, "text-danger fw-medium") if value else "-"
    
    def render_balance_amount(self, value):
        """Render balance with conditional coloring"""
        if not value:
            return self.render_amount(0, "text-muted")
        
        color_class = "text-danger fw-medium" if value > 0 else "text-success fw-medium"
        return self.render_amount(value, color_class)




class TransactionTable(BaseTable):
    created = None
    class Meta:
        model = Transaction
        fields = ("transaction_type", "voucher_number", "date", "branch", "narration", "invoice_amount", "total_amount")
        attrs = {"class": "table  table-vcenter text-nowrap table-bordered border-bottom table-striped"}


class JournalVoucherTable(BaseTable, StatusRendererMixin, AmountRendererMixin):
    """Journal Voucher Table"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data:
            record_ids = [record.pk for record in self.data]
            aggregates = Transaction.objects.filter(pk__in=record_ids).aggregate(
                total_amount=Sum('invoice_amount')
            )
            self.total_amount = aggregates['total_amount'] or Decimal('0')
        else:
            self.total_amount = Decimal('0')
    
    voucher_number = columns.TemplateColumn(
        template_code='''
            <a href="{{ record.get_update_url }}" 
               class="text-primary fw-medium text-decoration-none">
                {{ record.voucher_number }}
            </a>
        ''',
        verbose_name="Voucher #",
        attrs={
            "td": {"class": "text-primary fw-medium"},
            "th": {"class": "w-15"}
        },
        footer=""
    )
    
    date = columns.DateColumn(
        format="d M, Y",
        verbose_name="Date",
        attrs={
            "td": {"class": "text-nowrap"},
            "th": {"class": "w-12"}
        },
        footer=""
    )
    
    narration = columns.Column(
        verbose_name="Narration",
        attrs={
            "td": {"class": "text-muted small"},
            "th": {"class": "w-30"}
        },
        footer="Total"
    )
    
    invoice_amount = columns.Column(
        verbose_name="Amount",
        attrs={
            "td": {"class": "text-end fw-medium"},
            "th": {"class": "w-15 text-end"}
        },
        footer=lambda table: f"₹{table.total_amount:,.2f}"
    )
    
    status = columns.Column(
        verbose_name="Status",
        attrs={
            "td": {"class": "text-center"},
            "th": {"class": "w-10 text-center"}
        },
        footer=""
    )

    action = columns.TemplateColumn(
        template_code="""
            <div class="d-flex justify-content-center gap-2">
                <a href="{% url 'transactions:journalvoucher_update' record.pk %}" 
                class="btn btn-sm btn-outline-success" 
                title="Open Profile">
                    <i class="fe fe-eye"></i>
                </a>
            </div>
        """,
        orderable=False,
        verbose_name="Action",
    )
    
    def render_invoice_amount(self, value):
        return self.render_amount(value)
    
    class Meta(BaseTable.Meta):
        model = Transaction
        fields = (
            "voucher_number", "date", "branch", "invoice_amount", "narration", "status"
        )

    
class ContraVoucherTable(BaseTable, AmountRendererMixin):
    """Contra Voucher Table"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data:
            record_ids = [record.pk for record in self.data]
            aggregates = ContraVoucher.objects.filter(pk__in=record_ids).aggregate(
                total_amount=Sum('amount')
            )
            self.total_amount = aggregates['total_amount'] or Decimal('0')
        else:
            self.total_amount = Decimal('0')
    
    voucher_number = columns.TemplateColumn(
        template_code='''
            <a href="{{ record.get_absolute_url }}" 
               class="text-primary fw-medium text-decoration-none">
                {{ record.transaction.voucher_number }}
            </a>
        ''',
        accessor='transaction__voucher_number',
        verbose_name='Voucher #',
        attrs={
            "td": {"class": "text-primary fw-medium"},
            "th": {"class": "w-12"}
        },
        footer=""
    )
    
    date = columns.DateColumn(
        accessor='transaction__date',
        verbose_name='Date',
        format='d M, Y',
        attrs={
            "td": {"class": "text-nowrap"},
            "th": {"class": "w-10"}
        },
        footer=""
    )

    from_account = columns.Column(
        accessor='from_account__name',
        verbose_name='From Account',
        attrs={
            "td": {"class": "fw-medium"},
            "th": {"class": "w-18"}
        },
        footer=""
    )
    
    to_account = columns.Column(
        accessor='to_account__name',
        verbose_name='To Account',
        attrs={
            "td": {"class": "fw-medium"},
            "th": {"class": "w-18"}
        },
        footer=""
    )
    
    transfer_type = columns.Column(
        accessor='get_transfer_type',
        verbose_name='Transfer Type',
        orderable=False,
        attrs={
            "td": {"class": "text-center"},
            "th": {"class": "w-12 text-center"}
        },
        footer=""
    )
    
    amount = columns.Column(
        verbose_name='Amount',
        attrs={
            "td": {"class": "text-end fw-medium"},
            "th": {"class": "w-12 text-end"}
        },
        footer=lambda table: f"₹{table.total_amount:,.2f}"
    )
    
    transaction_mode = columns.Column(
        verbose_name='Mode',
        attrs={
            "td": {"class": "text-center text-capitalize"},
            "th": {"class": "w-10 text-center"}
        },
        footer="Total"
    )
    
    def render_amount(self, value):
        return super().render_amount(value)
    
    def render_transfer_type(self, value):
        type_badges = {
            'Cash Withdrawal': 'badge bg-warning',
            'Cash Deposit': 'badge bg-success',
            'Bank Transfer': 'badge bg-primary',
            'Cash Transfer': 'badge bg-info',
            'Fund Transfer': 'badge bg-secondary'
        }
        badge_class = type_badges.get(value, 'badge bg-light')
        return format_html(
            '<span class="{}">{}</span>',
            badge_class,
            value
        )
    
    def render_transaction_mode(self, value):
        if not value:
            return "-"
        
        mode_icons = {
            'cash': 'fas fa-money-bill-wave',
            'cheque': 'fas fa-money-check',
            'neft': 'fas fa-university',
            'rtgs': 'fas fa-university',
            'imps': 'fas fa-mobile-alt',
            'upi': 'fas fa-mobile-alt',
        }
        
        icon = mode_icons.get(value.lower(), 'fas fa-exchange-alt')
        return format_html(
            '<i class="{}"></i> {}',
            icon,
            value.upper()
        )
    
    class Meta(BaseTable.Meta):
        model = ContraVoucher
        fields = [
            'voucher_number', 'date', 'from_account', 'to_account',
            'transfer_type', 'amount', 'transaction_mode'
        ]


class IncomeExpenseTable(BaseTable, StatusRendererMixin, AmountRendererMixin):
    """Table for displaying Income and Expense entries"""
    
    voucher_number = columns.Column(
        accessor='transaction.voucher_number',
        verbose_name="Voucher #",
        linkify=lambda record: record.get_absolute_url(),
        attrs={
            "td": {"class": "text-primary fw-medium"},
            "th": {"class": "w-15"}
        }
    )
    
    date = columns.DateTimeColumn(
        accessor='date',
        format="d M, Y",
        verbose_name="Date",
        attrs={
            "td": {"class": "text-nowrap"},
            "th": {"class": "w-12"}
        }
    )
    
    type = columns.Column(
        verbose_name="Type",
        attrs={
            "td": {"class": "text-capitalize"},
            "th": {"class": "w-10"}
        }
    )
    
    party = columns.Column(
        accessor='party.name',
        verbose_name="Party",
        attrs={
            "td": {"class": "fw-normal"},
            "th": {"class": "w-20"}
        }
    )
    
    category = columns.Column(
        accessor='category.name',
        verbose_name="Category",
        attrs={
            "td": {"class": "fw-normal"},
            "th": {"class": "w-20"}
        }
    )
    
    amount = columns.Column(
        verbose_name="Amount",
        attrs={
            "td": {"class": "text-end fw-medium"},
            "th": {"class": "w-15 text-end"}
        }
    )
    
    reference_number = columns.Column(
        verbose_name="Ref #",
        attrs={
            "td": {"class": "text-muted"},
            "th": {"class": "w-10"}
        }
    )
    
    def render_type(self, value):
        type_badge_classes = {
            'income': 'badge bg-success',
            'expense': 'badge bg-danger',
        }
        badge_class = type_badge_classes.get(value, 'badge bg-secondary')
        display_value = value.replace('_', ' ').title()
        return format_html('<span class="{}">{}</span>', badge_class, display_value)
    
    def render_amount(self, value, record):
        from decimal import Decimal
        if value is None:
            return "₹0.00"
        
        # Determine color based on type
        color_class = "text-success fw-medium" if record.type == 'income' else "text-danger fw-medium"
        formatted = f"₹{value:,.2f}"
        return format_html('<span class="{}">{}</span>', color_class, formatted)
    
    def render_party(self, value):
        return value if value else "-"
    
    def render_category(self, value):
        return value if value else "-"
    
    class Meta(BaseTable.Meta):
        model = IncomeExpense
        fields = ( "reference_number", "voucher_number", "date", "type",  "branch", "party", "category", "amount",)
        attrs = {"class": "table table-vcenter text-nowrap table-bordered border-bottom table-striped"}

