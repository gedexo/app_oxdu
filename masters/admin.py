from core.base import BaseAdmin

from .models import Activity, Batch, BranchActivity, ChatSession, ComplaintRegistration, Course, Feedback, FeedbackAnswer, FeedbackQuestion, HeroBanner, Holiday, LeaveRequest, PdfBook, PlacementHistory, PublicMessage, Syllabus, BatchSyllabusStatus, SyllabusMaster, RequestSubmission, RequestSubmissionStatusHistory, Event, State
from django.contrib import admin


@admin.register(Batch)
class BatchAdmin(BaseAdmin):
    list_display = ("__str__", "branch", "course", "is_active",)
    search_fields = ("name", "branch")
    list_filter = ("branch", "course",)


@admin.register(Course)
class CourseAdmin(BaseAdmin):
    pass

@admin.register(PdfBook)
class PdfBookAdmin(BaseAdmin):
    pass

@admin.register(BatchSyllabusStatus)
class BatchSyllabusStatusAdmin(BaseAdmin):
    list_display = ("batch", "syllabus", "user", "status")

class BranchActivityInline(admin.TabularInline):
    model = BranchActivity
    extra = 1

@admin.register(Activity)
class ActivityAdmin(BaseAdmin):
    list_display = ("name",)
    inlines=[BranchActivityInline]

@admin.register(BranchActivity)
class BranchActivityAdmin(BaseAdmin):
    list_display = ('activity', 'branch', 'month', 'point',)


@admin.register(RequestSubmission)
class RequestSubmissionAdmin(BaseAdmin):
    list_display = ('request_id', 'title', 'branch_staff', "status", "is_request_completed", 'branch')
    
    
@admin.register(RequestSubmissionStatusHistory)
class RequestSubmissionStatusHistoryAdmin(BaseAdmin):
    list_display = ('submission', 'user', 'date', 'status')


class SyllabusInline(admin.TabularInline):
    model = Syllabus
    extra = 1

@admin.register(SyllabusMaster)
class SyllabusMasterAdmin(BaseAdmin):
    list_display = ('course', 'month', 'week',)
    inlines = [SyllabusInline]

@admin.register(LeaveRequest)
class LeaveRequestAdmin(BaseAdmin):
    list_display = ('student', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date', 'end_date', 'student__branch', 'student')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'reason')

@admin.register(FeedbackQuestion)
class FeedbackQuestionAdmin(BaseAdmin):
    list_display = ('order', 'feedback_type', 'question',)
    search_fields = ('question', 'feedback_type',)

@admin.register(FeedbackAnswer)
class FeedbackAnswerAdmin(BaseAdmin):
    list_display = ('question', 'answer_value', 'answer', 'is_active',)
    search_fields = ('answer',)

@admin.register(Feedback)
class FeedbackAdmin(BaseAdmin):
    list_display = ('student', 'question', 'answer',)

@admin.register(PlacementHistory)
class PlacementHistoryAdmin(BaseAdmin):
    list_display = ('student', 'company_name', 'designation', 'interview_type', 'interview_date', 'interview_status', 'attended_status', 'joining_status', 'is_active')

@admin.register(PublicMessage)
class PublicMessageAdmin(BaseAdmin):
    pass

@admin.register(Holiday)
class HolidayAdmin(BaseAdmin):
    list_display = ('name', 'date', 'is_active')


@admin.register(ComplaintRegistration)
class ComplaintRegistrationAdmin(BaseAdmin):
    pass 

@admin.register(HeroBanner)
class HeroBannerAdmin(BaseAdmin):
    pass

@admin.register(Event)
class EventAdmin(BaseAdmin):
    pass        

@admin.register(ChatSession)
class ChatSessionAdmin(BaseAdmin):
    pass

@admin.register(State)
class StateAdmin(BaseAdmin):
    pass
