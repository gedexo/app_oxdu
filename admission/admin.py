from django.contrib import admin
from core.base import BaseAdmin
from .models import FeeReceipt, AttendanceRegister, FeeStructure, Attendance, Admission, AdmissionEnquiry, PaymentMethod, StudentStageStatusHistory


class HasAttendanceFilter(admin.SimpleListFilter):
    title = 'Attendance'
    parameter_name = 'has_attendance'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'With Attendance'),
            ('no', 'Without Attendance'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(attendance__isnull=False)
        if self.value() == 'no':
            return queryset.filter(attendance__isnull=True)
        return queryset
    

class PaymentMethodInline(admin.TabularInline):
    model = PaymentMethod
    extra = 0
    
@admin.register(AttendanceRegister)
class AttendanceRegisterAdmin(BaseAdmin):
    list_filter = ("branch", "batch", "date", "course",HasAttendanceFilter)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_filter = ("register__course", "register__branch", 'student__batch', 'status')
    list_display = ('student', 'get_register_date', 'register', 'status')

    def get_register_date(self, obj):
        return obj.register.date 

    get_register_date.short_description = 'Register Date'


@admin.register(FeeStructure)
class FeeStructureAdmin(BaseAdmin):
    list_display = ("student", "transaction", "is_active",)

@admin.register(FeeReceipt)
class FeeReceiptAdmin(BaseAdmin):
    list_display = ("student", "status", "transaction", "created", "updated", "is_active",)
    inlines = [PaymentMethodInline  ]

@admin.register(Admission)
class AdmissionAdmin(BaseAdmin):
    list_display = ("fullname", "personal_email", "branch", "course", "batch", "batch_type", "is_active",)
    list_filter = ("branch", "course", "is_active")

@admin.register(AdmissionEnquiry)
class AdmissionEnquiryAdmin(BaseAdmin):
    list_display = ("full_name", "branch", "course", 'enquiry_type', 'status', 'tele_caller', "is_active",)
    list_filter = ("branch", "course", "is_active")

@admin.register(StudentStageStatusHistory)
class StudentStageStatusHistoryAdmin(BaseAdmin):
    list_display = ("student", "status", "remark", "created", "updated")