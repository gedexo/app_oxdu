from . import views
from django.urls import path


app_name = "admission"

urlpatterns = [
    #razorapy
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('verify-razorpay-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),

    #ajax
    path("<int:pk>/update-stage/", views.update_admission_stage, name="update_stage_status"),
    path('ajax/students-by-branch/', views.get_students_by_branch, name='get_students_by_branch'),
    path('enquiry/import/', views.ImportEnquiryView.as_view(), name='import_enquiry'),
    path("student_check_data/", views.student_check_data, name="student_check_data"),
    path('add-to-me/<int:pk>/', views.add_to_me, name='add_to_me'),
    path('bulk-add-to-me/', views.bulk_add_to_me, name='bulk_add_to_me'),
    path('assign-to/<int:pk>/', views.assign_to, name='assign_to'),
    path('bulk-assign-to/', views.assign_to, name='bulk_assign_to'),
    path('ajax/get-batches/', views.get_batches, name='get_batches_for_course'),
    path('admission/<int:pk>/update-stage/', views.admission_update_stage, name='admission_update_stage'),
    path('admission/bulk-update-stage/', views.bulk_update_student_stage, name='admission_bulk_update_stage'),
    path('get-batch-students/', views.get_batch_students, name='admission_get_batch_students'),
    path('get_student_fee_structure/', views.get_student_fee_structure, name='get_student_fee_structure'),
    path('api/student/<int:student_id>/calendar/', views.student_calendar_api, name='student_calendar_api'),
    path('remark/<int:pk>/history/', views.get_admission_history, name='get_admission_history'),
    path('remark-history/<int:pk>/update/', views.update_admission_history, name='update_remark_history'),
    path('ajax/calculate-fee-structure/', views.calculate_fee_structure_preview, name='calculate_fee_structure_preview'),
    path("student/<int:pk>/refresh-fee/", views.refresh_student_fee_structure, name="refresh_student_fee"),
    path("admission/refresh-fee/bulk/", views.bulk_refresh_fee_structure,name="bulk_refresh_fee" ),

    # admission
    path("all-admissions/", views.AllAdmissionListView.as_view(), name="all_admission_list"),
    path("admissions/", views.AdmissionListView.as_view(), name="admission_list"),
    path("inactive-admissions/", views.InactiveAdmissionListView.as_view(), name="inactive_admission_list"),
    path("course-wise-admissions/", views.CourseWiseAdmissionListView.as_view(), name="course_wise_admission_list"),
    path("batch-type-admissions/", views.BatchTypeAdmissionListView.as_view(), name="batch_type_admission_list"),
    path("admission/<str:pk>/", views.AdmissionDetailView.as_view(), name="admission_detail"),
    path("new/admission/", views.AdmissionCreateView.as_view(), name="admission_create"),
    path("admission/<str:pk>/update/", views.AdmissionUpdateView.as_view(), name="admission_update"),
    path("admission/<str:pk>/delete/", views.AdmissionDeleteView.as_view(), name="admission_delete"),
    path("admission/<str:pk>/profile/", views.AdmissionProfileDetailView.as_view(), name="admission_profile_detail"),
    path("due-students/", views.DueStudentsListView.as_view(), name="due_students_list"),
    path("student-certificate/<int:pk>/", views.StudentCertificateView.as_view(), name="student_certificate"),
    
    # enquiry
    path("leads/", views.LeadList.as_view(), name="lead_list"),
    path("public-leads/", views.PublicLeadListView.as_view(), name="public_lead_list"),
    path("assigned-leads/", views.AssignedLeadListView.as_view(), name="assigned_lead_list"),
    path("my-leads/", views.MyleadListView.as_view(), name="my_lead_list"),
    path("enquiries/", views.AdmissionEnquiryView.as_view(), name="admission_enquiry"),
    path("admission-enquiry/<str:pk>/", views.AdmissionEnquiryDetailView.as_view(), name="admission_enquiry_detail"),
    path("new/admission-enquiry/<int:pk>/", views.AdmissionEnquiryCreateView.as_view(), name="admission_enquiry_create"),
    path("new/admission-enquiry/", views.AdmissionEnquiryCreateView.as_view(), name="admission_enquiry_create"),
    path("admission-enquiry/<str:pk>/update/", views.AdmissionEnquiryUpdateView.as_view(), name="admission_enquiry_update"),
    path("admission-enquiry/<str:pk>/delete/", views.AdmissionEnquiryDeleteView.as_view(), name="admission_enquiry_delete"),
    path('enquiry/delete-unassigned/', views.DeleteUnassignedLeadsView.as_view(), name='delete_unassigned_leads'),
    
    #attendance
    path("attendance-registers/", views.AttendanceRegisterListView.as_view(), name="attendance_register_list"),
    path("attendance-register/<str:pk>/", views.AttendanceRegisterDetailView.as_view(), name="attendance_register_detail"),
    path("new/attendance-register/<int:pk>/", views.AttendanceRegisterCreateView.as_view(), name="attendance_register_create"),
    path("new/attendance-register/", views.AttendanceRegisterCreateView.as_view(), name="attendanceregister_create"),
    path("attendance-register/<str:pk>/update/", views.AttendanceRegisterUpdateView.as_view(), name="attendance_register_update"),
    path("attendance-register/<str:pk>/delete/", views.AttendanceRegisterDeleteView.as_view(), name="attendance_register_delete"),

    path('attendance-table/', views.StudentAttendanceTableView.as_view(), name='student_attendance_table'),
    path('api/attendance-data/', views.AttendanceTableDataAPIView.as_view(), name='attendance_data_api'),
    
    # Attendance API endpoints
    path("attendance/data/", views.attendance_data_api, name="attendance_data_api"),
    path("attendance/save/", views.attendance_save_api, name="attendance_save_api"),
    
    #FeeReceipt
    path("fee-receipts/", views.FeeReceiptListView.as_view(), name="fee_receipt_list"),
    path("fee-receipt/<str:pk>/", views.FeeReceiptDetailView.as_view(), name="fee_receipt_detail"),
    path("new/fee-receipt/<int:pk>/", views.FeeReceiptCreateView.as_view(), name="fee_receipt_create"),
    path("new/fee-receipt/", views.FeeReceiptCreateView.as_view(), name="feereceipt_create"),
    path("fee-receipt/<str:pk>/update/", views.FeeReceiptUpdateView.as_view(), name="fee_receipt_update"),
    path("fee-receipt/<str:pk>/delete/", views.FeeReceiptDeleteView.as_view(), name="fee_receipt_delete"),
    

    #FeeReceipt Report
    path("fee-receipt-report/", views.FeeReceiptReportView.as_view(), name="fee_receipt_report"),
    
    # Fee Overview
    path("students-fee-overview/", views.StudentFeeOverviewListView.as_view(), name="student_fee_overview_list"),
    path("students-fee-overview/<str:pk>/", views.StudentFeeOverviewDetailView.as_view(), name="student_fee_overview_detail"),
    
    # Student Fee Overview
    path("fee-overview/", views.FeeOverviewListView.as_view(), name="fee_overview_list"),
    
    #  registration form
    path('new/registration-form/', views.RegistrationView.as_view(), name='registration_form'),
    
    #terms-condition
    path("terms-condition/<str:pk>/", views.TermsConditionView.as_view(), name="terms_condition"),
    
    path("registration/<str:pk>/", views.RegistrationDetailView.as_view(), name="registration_detail")
]
