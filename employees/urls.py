from . import views
from django.urls import path
from . import api

app_name = "employees"

urlpatterns = [
    #API
    path('api/register-device/', api.RegisterDeviceView.as_view(), name='register_device'),
    path('api/my-devices/', api.get_my_devices, name='my_devices'),

    #ajax 
    path("get-salary/<int:pk>/", views.get_employee_salary, name="get_employee_salary"),
    path('ajax/get-employee-payrolls/', views.ajax_get_employee_payrolls, name='ajax_get_employee_payrolls'),
    path('ajax/payroll-data/', views.get_employee_payroll_data, name='ajax_get_employee_payroll_data'),
    path('leave-request/<int:pk>/update-status/', views.update_leave_status, name='update_leave_status'),
    path('ajax/get-payroll-data/', views.ajax_get_employee_payroll_data, name='ajax_get_employee_payroll_data'),


    #Appointment
    path("employee/appointment/<str:pk>/", views.EmployeeAppointmentPDFView.as_view(), name="employee_appointment"),
    path("share/appointment/<str:pk>/", views.share_employee_appointment, name="share_employee_appointment"),

    #Department 
    path("department/", views.DepartmentListView.as_view(), name="department_list"),
    path("department/<str:pk>/", views.DepartmentDetailView.as_view(), name="department_detail"),
    path("new/department/", views.DepartmentCreateView.as_view(), name="department_create"),
    path("department/<str:pk>/update/", views.DepartmentUpdateView.as_view(), name="department_update"),
    path("department/<str:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),

    #Designation
    path("designation/", views.DesignationListView.as_view(), name="designation_list"),
    path("designation/<str:pk>/", views.DesignationDetailView.as_view(), name="designation_detail"),
    path("new/designation/", views.DesignationCreateView.as_view(), name="designation_create"),
    path("designation/<str:pk>/update/", views.DesignationUpdateView.as_view(), name="designation_update"),
    path("designation/<str:pk>/delete/", views.DesignationDeleteView.as_view(), name="designation_delete"),

    #Employee
    path('profile/', views.ProfileView.as_view(), name='employee_profile'),
    path('profile/edit/<str:section>/', views.ProfileView.as_view(), name='profile_edit_section'),
    path('profile/update/<str:section>/', views.ProfileView.as_view(), name='profile_update_section'),
    path("employees/", views.EmployeeListView.as_view(), name="employee_list"),
    path("non-active-employees/", views.NonActiveEmployeeListView.as_view(), name="non_active_employee_list"),
    path("tele-callers/", views.TeleCallerListView.as_view(), name="tele_caller_list"),
    path("employees/add/", views.EmployeeCreateView.as_view(), name="employee_create"),
    path("view/<pk>/", views.EmployeeDetailView.as_view(), name="employee_detail"),
    path("employees/change/<pk>/", views.EmployeeUpdateView.as_view(), name="employee_update"),
    path("employees/delete/<pk>/", views.EmployeeDeleteView.as_view(), name="employee_delete"),

    #Payroll
    path("payroll/", views.PayrollListView.as_view(), name="payroll_list"),
    path("payroll/<str:pk>/", views.PayrollDetailView.as_view(), name="payroll_detail"),
    path("new/payroll/", views.PayrollCreateView.as_view(), name="payroll_create"),
    path("payroll/<str:pk>/update/", views.PayrollUpdateView.as_view(), name="payroll_update"),
    path("payroll/<str:pk>/delete/", views.PayrollDeleteView.as_view(), name="payroll_delete"),

    #payroll payment
    path("payments/", views.PayrollPaymentListView.as_view(), name="payroll_payment_list"),
    path("payments/create/", views.PayrollPaymentCreateView.as_view(), name="payroll_payment_create"),
    path("payments/detail/<str:pk>/", views.PayrollPaymentDetailView.as_view(), name="payroll_payment_detail"),
    path("payments/update/<str:pk>/", views.PayrollPaymentUpdateView.as_view(), name="payroll_payment_update"),
    path("payments/delete/<str:pk>/", views.PayrollPaymentDeleteView.as_view(), name="payroll_payment_delete"),

    #Advance Payroll Payment
    path("advance-payments/", views.AdvancePayrollPaymentListView.as_view(), name="advance_payroll_payment_list"),
    path("advance-payments/create/", views.AdvancePayrollPaymentCreateView.as_view(), name="advance_payroll_payment_create"),
    path("advance-payments/detail/<str:pk>/", views.AdvancePayrollPaymentDetailView.as_view(), name="advance_payroll_payment_detail"),
    path("advance-payments/update/<str:pk>/", views.AdvancePayrollPaymentUpdateView.as_view(), name="advance_payroll_payment_update"),
    path("advance-payments/delete/<str:pk>/", views.AdvancePayrollPaymentDeleteView.as_view(), name="advance_payroll_payment_delete"),

    #payroll reports
    path("payroll-reports/", views.PayrollReportView.as_view(), name="payroll_report"),
    path("inactive/payroll-reports/", views.InactivePayrollReportView.as_view(), name="inactive_payroll_report"),
    path("payroll-report/detail/<str:pk>/", views.PayrollReportDetailView.as_view(), name="payroll_report_detail"),
    path("payroll-report/slip/<str:pk>/", views.PayrollReportSlipView.as_view(), name="payroll_report_slip"),

    #partner
    path("partners/", views.PartnerListView.as_view(), name="partner_list"),
    path("partners/new/", views.PartnerCreateView.as_view(), name="partner_create"),
    path("partners/<str:pk>/", views.PartnerDetailView.as_view(), name="partner_detail"),
    path("partners/<str:pk>/edit/", views.PartnerUpdateView.as_view(), name="partner_update"),
    path("partners/<str:pk>/delete/", views.PartnerDeleteView.as_view(), name="partner_delete"),

    #employee leave request
    path("employee-leave-request/", views.EmployeeLeaveRequestListView.as_view(), name="employee_leave_request_list"),
    path("employee-leave-request/create/", views.EmployeeLeaveRequestCreateView.as_view(), name="employee_leave_request_create"),
    path("employee-leave-request/<int:pk>/", views.EmployeeLeaveRequestDetailView.as_view(), name="employee_leave_request_detail"),
    path("employee-leave-request/<str:pk>/update/", views.EmployeeLeaveRequestUpdateView.as_view(), name="employee_leave_request_update"),
    path("employee-leave-request/<str:pk>/delete/", views.EmployeeLeaveRequestDeleteView.as_view(), name="employee_leave_request_delete"),

    #employee leave request report
    path("employee-leave-report/", views.EmployeeLeaveReport.as_view(), name="employee_leave_report"),
    path("employee-leave-report/<str:pk>/", views.EmployeeLeaveReportDetailView.as_view(), name="employee_leave_report_detail"),
]
