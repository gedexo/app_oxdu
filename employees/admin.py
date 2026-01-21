from core.base import BaseAdmin

from .models import Department, Designation, Employee, Partner, Payroll, PayrollPayment, AdvancePayrollPayment
from django.contrib import admin


@admin.register(Department)
class DepartmentAdmin(BaseAdmin):
    list_display = ("name", "description", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("name",)
    

@admin.register(Employee)
class EmployeeAdmin(BaseAdmin):
    list_display = ("first_name", "branch", "employee_id", "is_active")
    list_filter = ("is_active",)
    search_fields = ("first_name", "branch__name", "employee_id")
    ordering = ("first_name",)


@admin.register(Payroll)
class PayrollAdmin(BaseAdmin):
    list_display = ("payroll_month", "basic_salary")
    list_filter = ("payroll_month",)
    search_fields = ("payroll_month", "basic_salary")
    ordering = ("payroll_month",)


@admin.register(PayrollPayment)
class PayrollPaymentAdmin(BaseAdmin):
    list_display = ("payment_date", "payroll", "employee", "amount_paid")
    list_filter = ("payment_date",)
    search_fields = ("payment_date", "amount_paid")
    ordering = ("payment_date",)


@admin.register(AdvancePayrollPayment)
class AdvancePayrollPaymentAdmin(BaseAdmin):
    list_display = ("payment_date", "payroll", "employee", "amount_paid")
    list_filter = ("payment_date",)
    search_fields = ("payment_date", "amount_paid")
    ordering = ("payment_date",)


@admin.register(Partner)
class PartnerAdmin(BaseAdmin):
    list_display = ("full_name", "contact_number", "whatsapp_number", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("full_name", "contact_number", "whatsapp_number", "email")
    ordering = ("-id",)