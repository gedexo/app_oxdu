from core.base import BaseTable, CustomBaseTable
import django_tables2 as tables
from .models import GroupMaster, Account
from transactions.models import Transaction
from core.base import columns
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from decimal import InvalidOperation
from decimal import Decimal
from django.utils.formats import number_format


class GroupMasterTable(BaseTable):
    name = columns.Column(verbose_name="Group Name")
    created = None

    action = columns.TemplateColumn(
        template_code="""
        <div class="btn-group btn-group-sm" role="group">
            <a href="{% url 'accounting:groupmaster_update' record.pk %}"
               class="btn btn-outline-primary"
               title="Edit">
                <i class="fe fe-file-text"></i>
            </a>
        </div>
        """,
        verbose_name="Actions",
        orderable=False,
    )

    class Meta(BaseTable.Meta):
        model = GroupMaster
        fields = ("name", "code", "branch", "nature_of_group", "main_group")

    def render_name(self, value, record):
        return f"{'— ' * record.level}{value}"

    
class AccountTable(BaseTable):
    account_info = columns.Column(verbose_name="Account", order_by='name', empty_values=())
    group_hierarchy = columns.Column(verbose_name="Group", order_by='under__name', empty_values=())
    balance = columns.Column(verbose_name="Current Balance")
    ledger_type_display = columns.Column(verbose_name="Type", orderable=False, empty_values=())
    credit_info = columns.Column(verbose_name="Credit Info", empty_values=(), orderable=False)
    created = None

    action = columns.TemplateColumn(
        template_code="""
        <div class="btn-group btn-group-sm" role="group">
            <a href="{% url 'accounting:account_update' record.pk %}"
               class="btn btn-outline-primary"
               title="Edit">
                <i class="fe fe-file-text"></i>
            </a>
        </div>
        """,
        verbose_name="Actions",
        orderable=False,
    )

    class Meta(BaseTable.Meta):
        model = Account
        fields = (
            "code",
            "branch",
            "account_info",
            "group_hierarchy",
            "ledger_type_display",
            "credit_info",
            "balance",
        )

    def render_account_info(self, record):
        """Render account name with alias and code"""
        account_url = reverse_lazy('accounting:account_list') + f'?account={record.id}'
        
        # Build name parts
        name_parts = [record.name]
        
        if record.alias_name:
            name_parts.append(f'<br><small class="text-muted">{record.alias_name}</small>')
        
        if record.is_locked and record.locking_account:
            name_parts.append(f'<br><span class="badge bg-warning-transparent"><i class="fa fa-lock"></i> Locked</span>')
        
        # Join all parts
        name_html = ''.join(name_parts)
        
        # Use mark_safe to prevent escaping
        return format_html(
            '<a href="{}" style="text-decoration:none; color:inherit;">{}</a>',
            account_url,
            mark_safe(name_html)
        )


    def render_group_hierarchy(self, record):
        """Render full group hierarchy path"""
        if record.under:
            hierarchy = record.under.get_full_path() if hasattr(record.under, 'get_full_path') else str(record.under)
            return format_html(
                '<small class="text-muted">{}</small>',
                hierarchy
            )
        return '-'

    def render_ledger_type_display(self, record):
        """Render ledger type with color badge"""
        type_colors = {
            "CUSTOMER": "primary",
            "SUPPLIER": "success",
            "EMPLOYEE": "info",
            "STAKE_HOLDER": "warning",
            "GENERAL": "secondary",
        }
        
        color = type_colors.get(record.ledger_type, "secondary")
        display_name = record.get_ledger_type_display()
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            display_name
        )

    def render_credit_info(self, record):
        """Render credit limit, credit days, and credit bill in same line."""
        info_parts = []
        
        if record.credit_limit:
            info_parts.append(f"₹{record.credit_limit:,.2f} L")
        
        if record.credit_days:
            info_parts.append(f"{record.credit_days} D")
        
        if record.credit_bill:
            info_parts.append(f"{record.credit_bill} B")
        
        if info_parts:
            return format_html(' | '.join(info_parts))
        else:
            return '-'

    def render_balance(self, record):
        """Render absolute balance with CR/DR and color-coded text."""
        try:
            balance = Decimal(str(record.balance))
        except (TypeError, InvalidOperation):
            balance = Decimal('0.00')

        abs_balance = abs(balance)
        formatted_balance = f"{abs_balance:.2f}"
        
        if balance > 0:
            # Debit -> Red
            return format_html(
                '<span style="color: #dc3545;">{} DR</span>', 
                formatted_balance
            )
        elif balance < 0:
            # Credit -> Green
            return format_html(
                '<span style="color: #198754;">{} CR</span>', 
                formatted_balance
            )
        else:
            # Zero balance -> Gray
            return format_html(
                '<span style="color: #6c757d;">0.00</span>'
            )


class TrialBalanceTable(tables.Table):
    # We use Column or TemplateColumn to ensure we can customize the rendering
    balance = tables.Column(empty_values=())
    debit = tables.Column(accessor='total_debit')
    credit = tables.Column(accessor='total_credit')

    class Meta:
        model = Account
        fields = ("code", "name", "group", "debit", "credit", "balance")
        attrs = {"class": "table table-vcenter text-nowrap table-bordered border-bottom table-striped accounting-table"}

    def render_debit(self, value):
        if value > 0:
            return number_format(value, decimal_pos=2)
        return "-"

    def render_credit(self, value):
        if value > 0:
            return number_format(value, decimal_pos=2)
        return "-"

    def render_balance(self, value):
        # Format the number to 2 decimal places with commas
        formatted_value = number_format(abs(value), decimal_pos=2)
        
        if value > 0:
            # Positive balance = Debit (Success/Green)
            return format_html(
                '<span class="text-success fw-bold">{} Dr</span>', 
                formatted_value
            )
        elif value < 0:
            # Negative balance = Credit (Danger/Red)
            return format_html(
                '<span class="text-danger fw-bold">{} Cr</span>', 
                formatted_value
            )
        else:
            return "0.00"