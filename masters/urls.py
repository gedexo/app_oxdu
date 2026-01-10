from . import views
from django.urls import path


app_name = "masters"

urlpatterns = [
    #ajax 
    path('syllabus/update-status/', views.update_syllabus_status, name='syllabus_status_update'),
    path('leave_request/<int:pk>/status/', views.leave_request_status_update, name='leave_request_status_update'),
    path('attendance/auto_mark_holiday/', views.auto_mark_holiday_api, name='auto_mark_holiday_api'),
    path('api/notifications/mark-read/<int:update_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/count/', views.NotificationCountAPI.as_view(), name='notification_count_api'),
    path("placement-request/<int:pk>/status/", views.placement_request_status_update, name="placement_request_status_update"),

    # Batch
    path("batch/list/", views.BatchListView.as_view(), name="batch_list"),
    path("batch/<str:pk>/detail/", views.BatchDetailView.as_view(), name="batch_detail"),
    path("batch/create/", views.BatchCreateView.as_view(), name="batch_create"),
    path("batch/<str:pk>/update/", views.BatchUpdateView.as_view(), name="batch_update"),
    path("batch/<str:pk>/delete/", views.BatchDeleteView.as_view(), name="batch_delete"),
    
    # Course
    path("course/list/", views.CourseListView.as_view(), name="course_list"),
    path("course/<str:pk>/detail/", views.CourseDetailView.as_view(), name="course_detail"),
    path("course/create/", views.CourseCreateView.as_view(), name="course_create"),
    path("course/<str:pk>/update/", views.CourseUpdateView.as_view(), name="course_update"),
    path("course/<str:pk>/delete/", views.CourseDeleteView.as_view(), name="course_delete"),
    
    # Pdf resource
    path("PDF-resource/list/", views.PDFBookResourceListView.as_view(), name="pdf_book_resource_list"),
    path("PDF-resource/<str:pk>/detail/", views.PDFBookResourceDetailView.as_view(), name="pdf_book_resource_detail"),
    path("new/PDF-resource/create/<str:pk>/", views.PDFBookResourceCreateView.as_view(), name="pdfbook_resource_create"),
    path("new/PDF-resource/create/", views.PDFBookResourceCreateView.as_view(), name="pdfbook_resource_create"),
    path("PDF-resource/<str:pk>/update/", views.PDFBookResourceUpdateView.as_view(), name="pdf_book_resource_update"),
    path("PDF-resource/<str:pk>/delete/", views.PDFBookResourceDeleteView.as_view(), name="pdf_book_resource_delete"),
    
    #Pdf List
    path("PDF/list/", views.PDFBookListView.as_view(), name="pdf_book_list"),
    # path("PDF/<str:pk>/detail/", views.PDFBookDetailView.as_view(), name="pdf_book_detail"),
    
    #Complaint
    path("complaint/list/", views.ComplaintListView.as_view(), name="complaint_list"),
    path("complaint/<str:pk>/detail/", views.ComplaintDetailView.as_view(), name="complaint_detail"),
    path("new/complaint/<str:pk>/", views.ComplaintCreateView.as_view(), name="complaint_create"),
    path("new/complaint/", views.ComplaintCreateView.as_view(), name="complaint_create"),
    path("complaint/<str:pk>/update/", views.ComplaintUpdateView.as_view(), name="complaint_update"),
    path("complaint/<str:pk>/delete/", views.ComplaintDeleteView.as_view(), name="complaint_delete"),

    #Update
    path("update/list/", views.UpdateListView.as_view(), name="update_list"),
    path("update/<str:pk>/detail/", views.UpdateDetailView.as_view(), name="update_detail"),
    path("new/update/<str:pk>/", views.UpdateCreateView.as_view(), name="update_create"),
    path("new/update/", views.UpdateCreateView.as_view(), name="update_create"),
    path("update/<str:pk>/update/", views.UpdateUpdateView.as_view(), name="update_update"),
    path("update/<str:pk>/delete/", views.UpdateDeleteView.as_view(), name="update_delete"),

    #Placement Request
    path("placement-requests/list/", views.PlacementRequestListView.as_view(), name="placement_request_list"),
    path("placement-request/<str:pk>/detail/", views.PlacementRequestDetailView.as_view(), name="placement_request_detail"),
    path("new/placement-request/<str:pk>/", views.PlacementRequestCreateView.as_view(), name="placement_request_create"),
    path("new/placement-request/", views.PlacementRequestCreateView.as_view(), name="placement_request_create"),
    path("placement-request/<str:pk>/update/", views.PlacementRequestUpdateView.as_view(), name="placement_request_update"),
    path("placement-request/<str:pk>/delete/", views.PlacementRequestDeleteView.as_view(), name="placement_request_delete"),

    # ==================== STUDENT CHAT URLS ====================
    path('student-chat/<int:user_id>/', views.StudentChatView.as_view(), name='student_chat'),
    path('student-chat/<int:user_id>/clear/', views.clear_student_chat, name='clear_student_chat'),
    path('student-chat/load-more/', views.load_more_student_messages, name='load_more_student_messages'),
    
    # ==================== EMPLOYEE CHAT URLS ====================
    path('chat/<int:user_id>/', views.ChatView.as_view(), name='chat_view'),
    path('chat/<int:user_id>/clear/', views.clear_employee_chat, name='clear_employee_chat'),
    path('chat/load-more/', views.load_more_employee_messages, name='load_more_employee_messages'),
    
    # Chat list
    path('employee-chat-list/', views.EmployeeChatListView.as_view(), name='employee_chat_list'),
    path('chat-list/', views.ChatListView.as_view(), name='chat_list'),
    
    # AJAX endpoints for real-time chat
    path('chat/send-message/', views.send_message_ajax, name='send_message_ajax'),
    
    #Syllabus Master
    path("course/syllabus-master/", views.CourseSyllabusMasterView.as_view(), name="course_syllabus_master"),
    path("syllabus-master/list/", views.SyllabusMasterList.as_view(), name="syllabus_master_list"),
    path("syllabus-master/<str:pk>/detail/", views.SyllabusMasterDetailView.as_view(), name="syllabus_master_detail"),
    path("syllabus-master/new/", views.SyllabusMasterCreateView.as_view(), name="syllabus_master_create"),
    path("syllabus-master/<str:pk>/update/", views.SyllabusMasterUpdateView.as_view(), name="syllabus_master_update"),
    path("syllabus-master/<str:pk>/delete/", views.SyllabusMasterDeleteView.as_view(), name="syllabus_master_delete"),

    #Syllabus
    path("syllabus/list/", views.SyllabusListView.as_view(), name="syllabus_list"),
    path("syllabus/<str:pk>/detail/", views.SyllabusDetailView.as_view(), name="syllabus_detail"),
    path("new/syllabus/", views.SyllabusCreateView.as_view(), name="syllabus_create"),
    path("syllabus/<str:pk>/update/", views.SyllabusUpdateView.as_view(), name="syllabus_update"),
    path("syllabus/<str:pk>/delete/", views.SyllabusDeleteView.as_view(), name="syllabus_delete"),

    #Course Syllabus
    path("course/syllabus/", views.CourseSyllabusView.as_view(), name="course_syllabus_list"),
    path("course/<int:pk>/syllabus/", views.CourseSyllabusView.as_view(), name="course_syllabus_list"),
    path("syllabus-report/<int:pk>/", views.SyllabusReportView.as_view(), name="syllabus_report"),
    path("syllabus-report/<int:pk>/details/", views.SyllabusReportView.as_view(), name="syllabus_report_details"),
    path("syllabus/<int:pk>/batch-report/", views.BatchSyllabusReportView.as_view(), name="batch_syllabus_report"),

    #student syllabus report
    path("student-syllabus-report/<int:pk>/", views.StudentSyllabusReportView.as_view(), name="student_syllabus_report"),

    #activity
    path("activities/", views.ActivityListView.as_view(), name="activity_list"),
    path("activity/<str:pk>/detail/", views.ActivityDetailView.as_view(), name="activity_detail"),
    path("activity/create/", views.ActivityCreateView.as_view(), name="activity_create"),
    path("activity/<str:pk>/update/", views.ActivityUpdateView.as_view(), name="activity_update"),
    path("activity/<str:pk>/delete/", views.ActivityDeleteView.as_view(), name="activity_delete"),

    #branch activity
    path("brach-activities/", views.BranchActivityListView.as_view(), name="branch_activity_list"),
    path("brach-activities-table/", views.BranchActivityTableView.as_view(), name="branch_activity_table"),
    path("branch-activity/<str:pk>/detail/", views.BranchActivityDetailView.as_view(), name="branch_activity_detail"),
    path("branch-activity/create/", views.BranchActivityCreateView.as_view(), name="branch_activity_create"),
    path("branch-activity/<str:pk>/update/", views.BranchActivityUpdateView.as_view(), name="branch_activity_update"),
    path("branch-activity/<str:pk>/delete/", views.BranchActivityDeleteView.as_view(), name="branch_activity_delete"),
    
    # Request Submission
    path("request-submission/", views.RequestSubmissionListView.as_view(), name="request_submission_list"),
    path("my-request-submission/", views.MyRequestSubmissionListView.as_view(), name="my_request_submission_list"),
    path("shared-requests/", views.SharedRequestsListView.as_view(), name="shared_requests_list"),
    path("request-submission/<str:pk>/", views.RequestSubmissionDetailView.as_view(), name="request_submission_detail"),
    path("new/request-submission/", views.RequestSubmissionCreateView.as_view(), name="request_submission_create"),
    path("request-submission/<str:pk>/update/", views.RequestStatusUpdateView.as_view(), name="request_submission_update"),
    path("request-submission/<str:pk>/delete/", views.RequestSubmissionDeleteView.as_view(), name="request_submission_delete"),
    
    path("request-submission-pdf/<str:pk>/", views.download_request_submission_pdf, name="request_submission_pdf"),
    path("request-submission-pdf/<str:pk>/download/", views.RequestSubmissionPDFDownloadView.as_view(), name="request_submission_pdf_download"),

    # Leave Request
    path("leave-requests/", views.LeaveRequestListView.as_view(), name="leave_request_list"),
    path("leave-requests/<str:pk>/", views.LeaveRequestDetailView.as_view(), name="leave_request_detail"),
    path("new/leave-request/", views.LeaveRequestCreateView.as_view(), name="leave_request_create"),
    path("leave-request/<str:pk>/update/", views.LeaveRequestUpdateView.as_view(), name="leave_request_update"),
    path("leave-request/<str:pk>/delete/", views.LeaveRequestDeleteView.as_view(), name="leave_request_delete"),

    #FeedbackQuestion
    path("feedback-questions/", views.FeedbackQuestionList.as_view(), name="feedback_question_list"),
    path("feedback-questions/<str:pk>/", views.FeedbackQuestionDetailView.as_view(), name="feedback_question_detail"),
    path("new/feedback-questions/", views.FeedbackQuestionCreateView.as_view(), name="feedback_question_create"),
    path("feedback-questions/<str:pk>/update/", views.FeedbackQuestionUpdateView.as_view(), name="feedback_question_update"),
    path("feedback-questions/<str:pk>/delete/", views.FeedbackQuestionDeleteView.as_view(), name="feedback_question_delete"),

    #Feedback
    path("feedbacks/", views.FeedbackListView.as_view(), name="feedback_list"),
    path("feedback/<str:pk>/", views.FeedbackDetailView.as_view(), name="feedback_detail"),
    path("new/feedback/", views.FeedbackCreateView.as_view(), name="feedback_create"),
    path("feedback/<str:pk>/update/", views.FeedbackUpdateView.as_view(), name="feedback_update"),
    path("feedback/<str:pk>/delete/", views.FeedbackDeleteView.as_view(), name="feedback_delete"),

    #Feedback Report
    path("feedback-report/", views.FeedbackReportView.as_view(), name="feedback_report"),
    
    #placement report
    path('placement-report/', views.PlacementReportView.as_view(), name='placement_report'),
    path('student/<int:pk>/placement-history/', views.StudentPlacementHistoryView.as_view(), name='student_placement_history'),
    path('student/<int:student_id>/placement-history/create/', views.PlacementHistoryCreateView.as_view(), name='placement_history_create'),
    path('placement-history/<int:pk>/update/', views.PlacementHistoryUpdateView.as_view(), name='placement_history_update'),
    path("placement-history/<str:pk>/delete/", views.PlacementHistoryDeleteView.as_view(), name="placement_history_delete"),

    #Public Message
    path('public-messages/', views.PublicMessageListView.as_view(), name='public_message_list'), 
    path('public-message/<str:pk>/detail/', views.PublicMessageDetailView.as_view(), name='public_message_detail'),
    path('new/public-message/', views.PublicMessageCreateView.as_view(), name='public_message_create'),
    path('public-message/<str:pk>/update/', views.PublicMessageUpdateView.as_view(), name='public_message_update'),
    path("public-message/<str:pk>/delete/", views.PublicMessageDeleteView.as_view(), name="public_message_delete"),

    #holiday
    path("holidays/", views.HolidayListView.as_view(), name="holiday_list"),
    path("holiday/<str:pk>/", views.HolidayDetailView.as_view(), name="holiday_detail"),
    path("new/holiday/", views.HolidayCreateView.as_view(), name="holiday_create"),
    path("holiday/<str:pk>/update/", views.HolidayUpdateView.as_view(), name="holiday_update"),
    path("holiday/<str:pk>/delete/", views.HolidayDeleteView.as_view(), name="holiday_delete"),

    #Hero Banner
    path("hero-banners/", views.HeroBannerListView.as_view(), name="hero_banner_list"),
    path("hero-banner/<str:pk>/", views.HeroBannerDetailView.as_view(), name="hero_banner_detail"),
    path("new/hero-banner/", views.HeroBannerCreateView.as_view(), name="hero_banner_create"),
    path("hero-banner/<str:pk>/update/", views.HeroBannerUpdateView.as_view(), name="hero_banner_update"),
    path("hero-banner/<str:pk>/delete/", views.HeroBannerDeleteView.as_view(), name="hero_banner_delete"),

    #events
    path("event/", views.EventView.as_view(), name="events"),
    path("event-lists/", views.EventListView.as_view(), name="event_list"),
    path("event/<str:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("new/event/", views.EventCreateView.as_view(), name="event_create"),
    path("event/<str:pk>/update/", views.EventUpdateView.as_view(), name="event_update"),
    path("event/<str:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),

]