from django_tables2 import columns
import django_tables2 as tables
from django.utils.html import format_html

from core.base import BaseTable
from .models import Department
from .models import Designation
from .models import Employee, Partner, Payroll, PayrollPayment, AdvancePayrollPayment, EmployeeLeaveRequest


class EmployeeTable(BaseTable):
    employee_id = columns.Column(linkify=True)
    created = None
    fullname = columns.Column(verbose_name="Name", order_by="first_name")
    total_salary = columns.Column(verbose_name="Monthly Salary")

    class Meta(BaseTable.Meta):
        model = Employee
        fields = ("employee_id", "branch", "fullname", "mobile", "department", "designation" , "employment_type", "total_salary", "is_active")

    
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

    
class EmployeeLeaveRequestTable(BaseTable):
    employee = tables.Column(linkify=True)
    created = None

    class Meta:
        model = EmployeeLeaveRequest
        fields = ("employee", "start_date", "end_date", "status", "reason")
        attrs = {"class": "table key-buttons table-bordered border-bottom table-hover"}