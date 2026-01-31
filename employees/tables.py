from django_tables2 import columns
import django_tables2 as tables
from django.utils.html import format_html
from django.urls import reverse_lazy
from django.utils import timezone

from core.base import BaseTable
from core.choices import LEAVE_STATUS_CHOICES
from .models import Department
from .models import Designation
from .models import Employee, Partner, Payroll, PayrollPayment, AdvancePayrollPayment, EmployeeLeaveRequest, EmployeeAttendanceRegister


class EmployeeTable(BaseTable):
    employee_id = columns.Column(linkify=True)
    created = None
    fullname = columns.Column(verbose_name="Name", order_by="first_name")
    total_salary = columns.Column(verbose_name="Monthly Salary")
    
    # Define the action column
    action = columns.Column(verbose_name="Action", orderable=False, empty_values=())

    class Meta(BaseTable.Meta):
        model = Employee
        fields = (
            "employee_id", "branch", "fullname", "mobile", 
            "department", "designation", "employment_type", 
            "total_salary", "is_active", "action"
        )

    def render_action(self, record):
        view_url = record.get_absolute_url()
        now = timezone.now()
        attendance_url = reverse_lazy("employees:employee_individual_attendance", kwargs={"pk": record.pk})
        attendance_query = f"?month={now.month}&year={now.year}"
        
        return format_html(
            '''
            <div class="d-flex align-items-center gap-2">
                <!-- View: Soft Blue Square -->
                <a href="{}" class="btn btn-sm border-0 rounded-2" 
                   title="View Profile"
                   style="background-color: #e2e8f0; color: #475569; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
                    <i class="fas fa-eye"></i>
                </a>

                <!-- Attendance: Soft Orange Square -->
                <a href="{}{}" target="_blank" class="btn btn-sm border-0 rounded-2" 
                   title="Attendance Report"
                   style="background-color: rgba(238, 76, 36, 0.15); color: #ee4c24; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
                    <i class="fas fa-calendar-check"></i>
                </a>
            </div>
            ''',
            view_url, attendance_url, attendance_query
        )

    def render_total_salary(self, value):
        """ Optional: Format salary with currency """
        return format_html('<span class="fw-bold">₹{}</span>', value) if value else "-"

    
class NonActiveEmployeeTable(BaseTable):
    employee_id = columns.Column(linkify=True)
    created = None
    fullname = columns.Column(verbose_name="Name", order_by="first_name")
    total_salary = columns.Column(verbose_name="Monthly Salary")

    class Meta(BaseTable.Meta):
        model = Employee
        fields = ("employee_id", "branch", "fullname", "mobile", "department", "designation" , "status", "user__is_active", "employment_type", "total_salary",)


class DepartmentTable(BaseTable):
    class Meta:
        model = Department
        fields = ("name", "department_lead")
        attrs = {"class": "table key-buttons border-bottom"}


class DesignationTable(BaseTable):
    class Meta:
        model = Designation
        fields = ("name", "description")
        attrs = {"class": "table key-buttons border-bottom"}


class PayrollTable(BaseTable):
    basic_salary = tables.Column(verbose_name="Basic Salary", accessor="basic_salary", orderable=True)
    allowances = tables.Column(verbose_name="Allowances", accessor="allowances", orderable=True)
    deductions = tables.Column(verbose_name="Deductions", accessor="deductions", orderable=True)
    overtime = tables.Column(verbose_name="Overtime", accessor="overtime", orderable=True)
    gross_salary = tables.Column(verbose_name="Gross Salary", accessor="gross_salary", orderable=True)
    net_salary = tables.Column(verbose_name="Net Salary", accessor="net_salary", orderable=True)

    class Meta:
        model = Payroll
        fields = (
            "payroll_year", 
            "payroll_month", 
            "employee", 
            "basic_salary", 
            "allowances", 
            "deductions", 
            "overtime", 
            "absences", 
            "gross_salary", 
            "net_salary"
        )
        attrs = {"class": "table key-buttons table-bordered border-bottom table-hover"}

    def render_basic_salary(self, value):
        return f"{value:,.0f}"

    def render_allowances(self, value):
        return f"{value:,.0f}"

    def render_deductions(self, value):
        return f"{value:,.0f}"

    def render_overtime(self, value):
        return f"{value:,.0f}"

    def render_gross_salary(self, value):
        return f"{value:,.0f}"

    def render_net_salary(self, value):
        return f"{value:,.0f}"


class PayrollPaymentTable(BaseTable):
    class Meta:
        model = PayrollPayment
        fields = ("employee", "payroll", "payment_date", "amount_paid")
        attrs = {"class": "table key-buttons border-bottom table-hover"} 

    
class AdvancePayrollPaymentTable(BaseTable):
    class Meta:
        model = AdvancePayrollPayment
        fields = ("employee", "payroll", "payment_date", "amount_paid",)
        attrs = {"class": "table key-buttons border-bottom table-hover"} 


class PayrollReportTable(BaseTable):
    employee = tables.Column()

    total_due = tables.Column(
        attrs={"td": {"class": "fw-bold"}, "th": {"class": "fw-bold"}}
    )
    total_paid = tables.Column(
        attrs={"td": {"class": "fw-bold"}, "th": {"class": "fw-bold"}}
    )
    pending_due = tables.Column(
        attrs={"td": {"class": "fw-bold"}, "th": {"class": "fw-bold"}}
    )
    advance_paid = tables.Column(
        attrs={"td": {"class": "fw-bold"}, "th": {"class": "fw-bold"}}
    )

    view_details = tables.Column()
    view_slip = tables.Column()
    created = None
    action = None

    class Meta:
        attrs = {"class": "table key-buttons table-bordered border-bottom table-hover"}
        fields = ("employee", "total_due", "total_paid", "pending_due", "advance_paid")

    
class PartnerTable(BaseTable):
    share_percentage = tables.Column(verbose_name="Share %")
    created = None

    class Meta:
        model = Partner
        fields = (
            "full_name",
            "email",
            "contact_number",
            "shares_owned",
            "share_percentage",
            "share_amount",
            "action",
        )
        attrs = {"class": "table key-buttons table-bordered border-bottom"}

    def render_share_percentage(self, record):
        return format_html(
            '<span class="fw-bold">{}</span>',
            f"{record.share_percentage} %"
        )

    def render_share_amount(self, record):
        return format_html(
            '<span class="text-success fw-bold">{}</span>',
            f"₹{record.share_amount:,.0f}"
        )

    
class EmployeeLeaveRequestTable(tables.Table):
    action = columns.TemplateColumn(
        """
        <div class="d-flex text-start">
            {% if record.status == "pending" %}
                {% if request.user.is_superuser or request.user.is_staff or request.user.groups.all.0.name == "hr" %}
                    <a href="javascript:void(0);" class="action-btns1 approve-btn me-1" data-id="{{ record.pk }}" data-action="approved" title="Approve">
                        <i class="fe fe-check text-success"></i>
                    </a>

                    <a href="javascript:void(0);" class="action-btns1 reject-btn me-1" data-id="{{ record.pk }}" data-action="rejected" title="Reject">
                        <i class="fe fe-x text-danger"></i>
                    </a>
                {% endif %}
            {% endif %}

            <a href="{{ record.get_absolute_url }}" class="action-btns1 me-1" title="View">
                <i class="fe fe-eye text-primary"></i>
            </a>

            {% if request.user.is_superuser or request.user.is_staff %}
                <a href="{{ record.get_delete_url }}" class="action-btns1" data-bs-toggle="tooltip" title="Delete">
                    <i class="fe fe-trash-2 text-danger"></i>
                </a>
            {% endif %}
        </div>
        """,
        orderable=False,
    )

    total_days = tables.Column(verbose_name="Days", orderable=False)

    class Meta:
        model = EmployeeLeaveRequest
        fields = (
            "employee",
            "leave_type",
            "start_date",
            "end_date",
            "total_days",   
            "reason",
            "status",
            "created",
        )
        attrs = {"class": "table table-striped table-bordered border-bottom table-hover"}

        row_attrs = {
            "class": lambda record: (
                "table-success" if record.status == "approved" else
                "table-danger" if record.status == "rejected" else
                "table-warning" if record.status == "pending" else
                ""
            )
        }

    def render_total_days(self, value, record):
        days = record.total_days

        if days <= 2:
            color = "#198754"   # green
        elif days <= 5:
            color = "#ffc107"   # yellow
        else:
            color = "#dc3545"   # red

        label = "day" if days == 1 else "days"

        return format_html(
            '<strong style="color:{};">{} {}</strong>',
            color,
            days,
            label
        )

    def render_status(self, value, record=None):
        key = (value or "").strip().lower()

        status_map = {
            "approved": {
                "css": "badge badge-success text-bg-success",
                "style": "background:#198754;color:#fff",
            },
            "rejected": {
                "css": "badge badge-danger text-bg-danger",
                "style": "background:#dc3545;color:#fff",
            },
            "pending": {
                "css": "badge badge-warning text-bg-warning",
                "style": "background:#ffc107;color:#fff",
            },
            "cancelled": {
                "css": "badge badge-secondary text-bg-secondary",
                "style": "background:#6c757d;color:#fff",
            },
        }

        config = status_map.get(key, {
            "css": "badge badge-info text-bg-info",
            "style": "background:#17a2b8;color:#fff",
        })

        # Get label from choices if available
        label = dict(LEAVE_STATUS_CHOICES).get(value, value or "")

        return format_html(
            '<span class="{}" style="padding:0.275rem 0.65rem;{}">{}</span>',
            config["css"],
            config["style"],
            label,
        )

    
class EmployeeLeaveReportTable(BaseTable):
    fullname = tables.Column(
        accessor='fullname', 
        verbose_name="Name", 
        order_by=("first_name", "last_name")
    )
    
    total_balance_leaves = tables.Column(
        verbose_name="Balance Paid Leave", 
        accessor="total_balance_leaves"
    )
    
    total_balance_wfh = tables.Column(
        verbose_name="Balance WFH", 
        accessor="total_balance_wfh"
    )

    action = tables.TemplateColumn(
        template_code='''
            <div class="text-center">
                <a href="{% url 'employees:employee_leave_report_detail' record.pk %}" 
                   class="btn btn-sm" 
                   style="background-color: #eef2ff; color: #ee4c24; border: 1px solid #ee4c24; font-weight: 500; padding: 0.4rem 0.8rem; border-radius: 8px; transition: all 0.3s ease;">
                    <i class="fas fa-external-link-alt me-1" style="font-size: 0.8rem;"></i> 
                    Details
                </a>
            </div>
        ''',
        verbose_name="Action",
        orderable=False,
        exclude_from_export=True
    )

    created = None

    class Meta:
        model = Employee
        fields = (
            "fullname",
            "department",
            "designation",
            "total_balance_leaves",
            "total_balance_wfh",
            "action",
        )
        attrs = {"class": "table table-bordered border-bottom table-hover"}

    
class EmployeeAttendanceTable(BaseTable):
    class Meta:
        model = EmployeeAttendanceRegister
        fields = (
            "employee",
            "date",
            "status",
        )
        attrs = {"class": "table table-bordered border-bottom table-hover"}
