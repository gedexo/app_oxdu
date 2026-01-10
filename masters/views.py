import sys
import json
import logging
from itertools import groupby
from django.db.models import Max
from firebase_admin import messaging
from django.utils import timezone
from django.db.models.functions import Coalesce
from fcm_django.models import FCMDevice
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.http import HttpResponse
from datetime import datetime, timedelta
from urllib.parse import urlencode
from reportlab.pdfgen import canvas
from core.pdfview import PDFView
from django.views.generic.base import ContextMixin
from dateutil.relativedelta import relativedelta
from django.views.generic.edit import CreateView
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Avg, OuterRef, Subquery, IntegerField, Exists, DateTimeField
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.forms import HiddenInput, MultipleChoiceField, MultipleHiddenInput, formset_factory, inlineformset_factory, model_to_dict

from django.db import IntegrityError

from django.db import transaction
from django.urls import reverse_lazy
from core import mixins
from admission.models import Admission, Attendance, AttendanceRegister
from employees.models import Employee
from core.choices import SYLLABUS_MONTH_CHOICE, USERTYPE_CHOICES, USERTYPE_FLOW_CHOICES, FEEDBACK_TYPE_CHOICES
from branches.models import Branch

from . import forms
from . import tables
from .forms import FeedbackAnswerFormSet, FeedbackForm, PdfBookFormSet, SyllabusForm, ChatMessageForm, SyllabusMasterForm, SyllabusFormSet
from .models import Activity, Batch, BranchActivity, ComplaintRegistration, Course, Feedback, FeedbackAnswer, FeedbackQuestion, HeroBanner, Holiday, LeaveRequest, PDFBookResource, PdfBook, PlacementHistory, PublicMessage, Syllabus, ChatSession, SyllabusMaster, Update, PlacementRequest, RequestSubmission, RequestSubmissionStatusHistory, BatchSyllabusStatus, Event
from admission.utils import send_sms
User = get_user_model()

logger = logging.getLogger(__name__)

@login_required
def load_more_student_messages(request):
    """Load more messages for student chat"""
    other_user_id = request.GET.get('other_user_id')
    offset = int(request.GET.get('offset', 20))
    latest_message_id = request.GET.get('latest_message_id')
    limit = 20
    
    other_user = get_object_or_404(User, id=other_user_id)
    current_user = request.user
    
    # Build query
    message_query = ChatSession.objects.filter(
        Q(sender=current_user, recipient=other_user) |
        Q(sender=other_user, recipient=current_user)
    ).select_related('sender', 'recipient').only(
        'id', 'message', 'attachment', 'created', 'sender', 'recipient', 'read', 'deleted_by_ids'
    )
    
    # If latest_message_id is provided, fetch newer messages
    if latest_message_id:
        message_query = message_query.filter(id__gt=latest_message_id)
        # Get all newer messages, no offset/pagination needed for new messages
        all_messages = message_query.order_by('created')  # Chronological order for new messages
        
        # Filter deleted messages in Python
        filtered_messages = [msg for msg in all_messages if current_user.id not in msg.deleted_by_ids]
        
        messages_data = []
        for message in filtered_messages:
            messages_data.append({
                'id': message.id,
                'message': message.message,
                'attachment_url': message.attachment.url if message.attachment else None,
                'attachment_name': message.attachment.name if message.attachment else None,
                'time': message.created.strftime('%I:%M %p'),
                'timestamp': message.created.isoformat(),
                'is_sent': message.sender == current_user,
                'is_read': message.read,
            })
        
        return JsonResponse({
            'messages': messages_data,
            'offset': offset,
            'has_more': False  # For new messages, we don't have pagination
        })
    else:
        # Original behavior: load older messages
        all_messages = message_query.order_by('-created')
        
        # Filter deleted messages in Python and apply pagination
        filtered_messages = [msg for msg in all_messages if current_user.id not in msg.deleted_by_ids]
        messages = filtered_messages[offset:offset+limit]
        
        messages_data = []
        for message in reversed(messages):
            messages_data.append({
                'id': message.id,
                'message': message.message,
                'attachment_url': message.attachment.url if message.attachment else None,
                'attachment_name': message.attachment.name if message.attachment else None,
                'time': message.created.strftime('%I:%M %p'),
                'timestamp': message.created.isoformat(),
                'is_sent': message.sender == current_user,
                'is_read': message.read,
            })
        
        total_messages = len(filtered_messages)
        
        return JsonResponse({
            'messages': messages_data,
            'offset': offset + limit,
            'has_more': (offset + limit) < total_messages
        })


@csrf_exempt 
def clear_student_chat(request, user_id):
    """Clear student chat for current user only (WhatsApp-style)"""
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Get all messages between these two users
    messages = ChatSession.objects.filter(
        Q(sender=current_user, recipient=other_user) |
        Q(sender=other_user, recipient=current_user)
    )
    
    # Mark each message as deleted for current user only
    for message in messages:
        if current_user.id not in message.deleted_by_ids:
            message.deleted_by_ids.append(current_user.id)
            message.save(update_fields=['deleted_by_ids'])
    
    return JsonResponse({'status': 'success'})


# ==================== EMPLOYEE CHAT VIEWS ====================


@login_required
def load_more_employee_messages(request):
    """Load more messages for employee chat"""
    other_user_id = request.GET.get('other_user_id')
    offset = int(request.GET.get('offset', 20))
    latest_message_id = request.GET.get('latest_message_id')
    limit = 20
    
    other_user = get_object_or_404(User, id=other_user_id)
    current_user = request.user
    
    # Build query
    message_query = ChatSession.objects.filter(
        Q(sender=current_user, recipient=other_user) |
        Q(sender=other_user, recipient=current_user)
    ).select_related('sender', 'recipient').only(
        'id', 'message', 'attachment', 'created', 'sender', 'recipient', 'read', 'deleted_by_ids'
    )
    
    # If latest_message_id is provided, fetch newer messages
    if latest_message_id:
        message_query = message_query.filter(id__gt=latest_message_id)
        # Get all newer messages, no offset/pagination needed for new messages
        all_messages = message_query.order_by('created')  # Chronological order for new messages
        
        # Filter deleted messages in Python
        filtered_messages = [msg for msg in all_messages if current_user.id not in msg.deleted_by_ids]
        
        messages_data = []
        for message in filtered_messages:
            messages_data.append({
                'id': message.id,
                'message': message.message,
                'attachment_url': message.attachment.url if message.attachment else None,
                'attachment_name': message.attachment.name if message.attachment else None,
                'time': message.created.strftime('%I:%M %p'),
                'timestamp': message.created.isoformat(),
                'is_sent': message.sender == current_user,
                'is_read': message.read,
            })
        
        return JsonResponse({
            'messages': messages_data,
            'offset': offset,
            'has_more': False  # For new messages, we don't have pagination
        })
    else:
        # Original behavior: load older messages
        all_messages = message_query.order_by('-created')
        
        # Filter deleted messages in Python and apply pagination
        filtered_messages = [msg for msg in all_messages if current_user.id not in msg.deleted_by_ids]
        messages = filtered_messages[offset:offset+limit]
        
        messages_data = []
        for message in reversed(messages):
            messages_data.append({
                'id': message.id,
                'message': message.message,
                'attachment_url': message.attachment.url if message.attachment else None,
                'attachment_name': message.attachment.name if message.attachment else None,
                'time': message.created.strftime('%I:%M %p'),
                'timestamp': message.created.isoformat(),
                'is_sent': message.sender == current_user,
                'is_read': message.read,
            })
        
        total_messages = len(filtered_messages)
        
        return JsonResponse({
            'messages': messages_data,
            'offset': offset + limit,
            'has_more': (offset + limit) < total_messages
        })


@csrf_exempt 
def clear_employee_chat(request, user_id):
    """Clear employee chat for current user only (WhatsApp-style)"""
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Get all messages between these two users
    messages = ChatSession.objects.filter(
        Q(sender=current_user, recipient=other_user) |
        Q(sender=other_user, recipient=current_user)
    )
    
    # Mark each message as deleted for current user only
    for message in messages:
        if current_user.id not in message.deleted_by_ids:
            message.deleted_by_ids.append(current_user.id)
            message.save(update_fields=['deleted_by_ids'])
    
    return JsonResponse({'status': 'success'})


def student_syllabus_redirect(request):
    if request.user.is_authenticated and request.user.usertype == "student":
        admission = Admission.objects.filter(user=request.user).first()
        if admission and admission.course:
            return redirect("masters:syllabus_detail", course_id=admission.course.id)
    return redirect("core:home")


@csrf_exempt
def update_syllabus_status(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."})

    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "User not authenticated."})

    try:
        data = json.loads(request.body)
        syllabus_id = data.get("syllabus_id")
        if not syllabus_id:
            return JsonResponse({"success": False, "error": "Syllabus ID not provided."})

        syllabus = Syllabus.objects.get(id=syllabus_id)

        # ---- If / Elif / Else logic for user types ----
        if request.user.usertype == "student":
            # Get batch via Admission model
            admission = Admission.objects.filter(user=request.user).first()
            if not admission or not admission.batch:
                return JsonResponse({"success": False, "error": "No batch assigned to student."})
            batch = admission.batch

        elif request.user.usertype == "teacher":
            # For teachers, get batch via batch_id in AJAX or pick first batch related to syllabus
            batch_id = data.get("batch_id")
            if batch_id:
                batch = Batch.objects.filter(id=batch_id).first()
            else:
                # fallback: pick first batch related to this syllabus
                batch = syllabus.syllabus_master.course.batch_set.first()  # adjust according to your model
            if not batch:
                return JsonResponse({"success": False, "error": "No batch found for teacher."})

        else:
            return JsonResponse({"success": False, "error": "Only students and teachers can change status."})

        # ---- Update status ----
        status_obj, created = BatchSyllabusStatus.objects.get_or_create(
            syllabus=syllabus,
            user=request.user,
            batch=batch
        )
        status_obj.status = "completed"
        status_obj.save()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@csrf_exempt
def leave_request_status_update(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    leave = LeaveRequest.objects.filter(pk=pk).first()
    if not leave:
        return JsonResponse({"success": False, "error": "Leave not found"})

    try:
        data = json.loads(request.body)
        status = data.get("status")

        if status not in ["approved", "rejected"]:
            return JsonResponse({"success": False, "error": "Invalid status"})

        # ✅ Update leave request status
        leave.status = status
        leave.approved_by = getattr(request.user, "employee", None)
        leave.approved_date = timezone.now()
        leave.save()

        student = leave.student
        start_date = leave.start_date
        end_date = leave.end_date
        current_date = start_date

        while current_date <= end_date:
            try:
                register, _ = AttendanceRegister.objects.get_or_create(
                    branch=student.branch,
                    batch=student.batch,
                    course=student.course,
                    date=current_date,
                )

                # ✅ Mark attendance differently for approved and rejected
                if status == "approved":
                    Attendance.objects.update_or_create(
                        student=student,
                        register=register,
                        defaults={"status": "Absent"},
                    )
                elif status == "rejected":
                    Attendance.objects.update_or_create(
                        student=student,
                        register=register,
                        defaults={"status": "Absent"},  # still absent, but...
                    )
            except Exception as e:
                print(f"Error updating attendance for {student.fullname()} on {current_date}: {e}")
            current_date += timedelta(days=1)

        return JsonResponse({"success": True})

    except Exception as e:
        print(f"Error in leave_request_status_update: {e}")
        return JsonResponse({"success": False, "error": str(e)})


@csrf_exempt
def auto_mark_holiday_api(request):
    """
    API endpoint to automatically mark attendance as 'Holiday' 
    for all students on a specific date.
    """
    try:
        from admission.models import Admission, AttendanceRegister, Attendance
        
        date_str = request.GET.get('date')
        if not date_str:
            return JsonResponse({'error': 'Date parameter is required'}, status=400)
        
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        # Check if date is in future
        if selected_date > timezone.now().date():
            return JsonResponse({'error': 'Cannot mark holiday for future dates'}, status=400)

        # Get active holidays for the selected date
        holidays = Holiday.objects.filter(
            is_active=True, 
            date=selected_date
        )

        if not holidays.exists():
            return JsonResponse({'error': 'No holiday found for the selected date'}, status=400)

        total_students = 0
        total_registers = 0

        with transaction.atomic():
            for holiday in holidays:
                # Get all active students
                students = Admission.objects.filter(
                    is_active=True,
                    stage_status='active',
                    batch__status='in_progress'
                ).select_related('batch', 'course', 'branch')

                # Apply branch filter if holiday is branch-specific
                if holiday.scope == 'branch' and holiday.branch.exists():
                    branch_ids = holiday.branch.values_list('id', flat=True)
                    students = students.filter(branch_id__in=branch_ids)

                if not students.exists():
                    continue

                # Group students by batch, course, branch
                grouped = {}
                for student in students:
                    if student.batch and student.course and student.branch:
                        key = (student.batch_id, student.course_id, student.branch_id)
                        grouped.setdefault(key, []).append(student)

                for (batch_id, course_id, branch_id), batch_students in grouped.items():
                    # Get or create attendance register
                    register, created = AttendanceRegister.objects.get_or_create(
                        date=selected_date,
                        batch_id=batch_id,
                        course_id=course_id,
                        branch_id=branch_id,
                        defaults={'is_active': True}
                    )

                    # Delete existing attendance records for this register
                    Attendance.objects.filter(register=register).delete()

                    # Create holiday attendance records
                    attendance_objects = []
                    for student in batch_students:
                        attendance_objects.append(
                            Attendance(
                                register=register,
                                student=student,
                                status='Holiday',
                                sms_sent=True
                            )
                        )

                    # Bulk create attendance records
                    if attendance_objects:
                        Attendance.objects.bulk_create(attendance_objects)
                        total_students += len(attendance_objects)
                        total_registers += 1

        return JsonResponse({
            'success': True,
            'message': f'Holiday marked successfully for {total_students} students',
            'total_students': total_students,
            'total_registers': total_registers,
            'date': selected_date.strftime('%Y-%m-%d')
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods

@method_decorator(cache_page(30), name='dispatch')
class NotificationCountAPI(View):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                from masters.models import Update, NotificationReadStatus
                
                # Count only unread notifications
                unread_count = Update.objects.filter(
                    is_active=True, 
                    is_notification=True
                ).exclude(
                    notificationreadstatus__user=request.user
                ).count()
                
                return JsonResponse({'count': unread_count})
            except Exception as e:
                return JsonResponse({'count': 0})
        return JsonResponse({'count': 0})
    

@require_http_methods(["POST"])
def mark_notification_read(request, update_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Not authenticated'})
    
    try:
        from masters.models import Update, NotificationReadStatus
        
        update = Update.objects.get(id=update_id, is_active=True)
        
        # Mark as read
        NotificationReadStatus.objects.get_or_create(
            user=request.user,
            update=update
        )
        
        return JsonResponse({'status': 'success'})
        
    except Update.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Update not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Not authenticated'})
    
    try:
        from masters.models import Update, NotificationReadStatus
        
        # Get all unread notifications
        unread_updates = Update.objects.filter(
            is_active=True, 
            is_notification=True
        ).exclude(
            notificationreadstatus__user=request.user
        )
        
        # Mark all as read
        for update in unread_updates:
            NotificationReadStatus.objects.get_or_create(
                user=request.user,
                update=update
            )
        
        return JsonResponse({'status': 'success', 'marked_read': unread_updates.count()})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

    
@login_required
@require_POST
def placement_request_status_update(request, pk):
    # 🔐 Permission check
    if request.user.usertype not in [
        "admin_staff", "mentor", "hr", "ceo", "cfo", "coo"
    ]:
        return JsonResponse(
            {"error": "Permission denied"},
            status=403
        )

    placement = get_object_or_404(PlacementRequest, pk=pk)

    new_status = request.POST.get("status")

    # ✅ Validate status
    valid_statuses = dict(
        PlacementRequest._meta.get_field("status").choices
    )

    if new_status not in valid_statuses:
        return JsonResponse(
            {"error": "Invalid status"},
            status=400
        )

    placement.status = new_status
    placement.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "status": new_status
    })
    

class BatchListView(mixins.HybridListView):
    model = Batch
    table_class = tables.BatchTable
    filterset_fields = {'course': ['exact'], "branch": ['exact'], "starting_date": ['exact'], "ending_date": ['exact'], "starting_time": ['exact'], "ending_time": ['exact'] }
    permissions = ("branch_staff", "partner", "teacher", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    
    def get_queryset(self):
        if self.request.user.usertype == "teacher":
            try:
                teacher = Employee.objects.get(user=self.request.user)
                qs = super().get_queryset().filter(course=teacher.course, branch=self.request.user.branch, is_active=True)
            except Employee.DoesNotExist:
                qs = Batch.objects.none()
        elif self.request.user.usertype == "branch_staff":
            qs = super().get_queryset().filter(branch=self.request.user.branch, is_active=True)
        else:
            qs = super().get_queryset().filter(is_active=True)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_master"] = True
        context["is_batch"] = True
        context["can_add"] = self.request.user.usertype in ["admin_staff", "mentor", "ceo","cfo","coo","hr","cmo"] or self.request.user.is_superuser
        context["new_link"] = reverse_lazy("masters:batch_create")
        return context

    
class BatchDetailView(mixins.HybridDetailView):
    model = Batch
    permissions = ("branch_staff", "mentor", "admin_staff", "teacher", "is_superuser", "ceo","cfo","coo","hr","cmo")
    

class BatchCreateView(mixins.HybridCreateView):
    model = Batch
    fields = [
        "course",
        "branch",
        "batch_name",
        "starting_date",
        "ending_date",
        "starting_time",
        "ending_time",
        "description",
        "status"
    ]
    exclude = None
    permissions = ("is_superuser", "mentor", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Batch"
        return context

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super(mixins.HybridCreateView, self).form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)
    

class BatchUpdateView(mixins.HybridUpdateView):
    model = Batch
    fields = [
        "course",
        "branch",
        "batch_name",
        "starting_date",
        "ending_date",
        "starting_time",
        "ending_time",
        "description",
        "status"
    ]
    permissions = ("is_superuser", "mentor", "admin_staff", "ceo","cfo","coo","hr","cmo")


class BatchDeleteView(mixins.HybridDeleteView):
    model = Batch
    permissions = ("is_superuser", "mentor", "admin_staff", "ceo","cfo","coo","hr","cmo")
    

class CourseListView(mixins.HybridListView):
    model = Course
    table_class = tables.CourseTable
    filterset_fields = {'name': ['exact'], }
    permissions = ("branch_staff", "partner", "teacher", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "tele_caller", "sales_head", "mentor")
    branch_filter = False
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_course"] = True 
        context["is_master"] = True
        return context
    

class CourseDetailView(mixins.HybridDetailView):
    model = Course
    permissions = ("branch_staff", "partner", "admin_staff", "teacher", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "masters/course/course_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_course_detail"] = True
        context["is_master"] = True
        context["title"] = "Course Detail"
        return context
    

class CourseCreateView(mixins.HybridCreateView):
    model = Course
    permissions = ("is_superuser","admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "New Course"
        return context

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)
    

class CourseUpdateView(mixins.HybridUpdateView):
    model = Course
    fields = "__all__"
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class CourseDeleteView(mixins.HybridDeleteView):
    model = Course
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class PDFBookResourceListView(mixins.HybridListView):
    model = PDFBookResource
    table_class = tables.PDFBookResourceTable
    filterset_fields = ('course',)
    permissions = ("superadmin", "partner", 'branch_staff', "admin_staff", 'teacher', "student", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.usertype == "teacher":
            try:
                teacher = Employee.objects.get(user=user)
                queryset = queryset.filter(course=teacher.course)
            except Employee.DoesNotExist:
                queryset = PDFBookResource.objects.none() 

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "PDF Resource List"
        context["is_pdf_resource"] = True
        context["is_master"] = True
        context["can_add"] = True
        context["new_link"] = reverse_lazy("masters:pdfbook_resource_create")
        return context


class PDFBookResourceDetailView(mixins.HybridDetailView):
    model = PDFBookResource
    template_name = "masters/pdfbook/object_view.html"
    permissions = ("superadmin", "partner", "branch_staff", "admin_staff",  "teacher", "student", "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.get_object()

        pdfbook_entries = PdfBook.objects.filter(resource=resource, is_active=True)

        context["customer_table"] = tables.PDFBookResourceTable(pdfbook_entries)
        context["pdfbook_entries"] = pdfbook_entries 
        return context


class PDFBookResourceCreateView(mixins.HybridCreateView):
    model = PDFBookResource
    permissions = ("superadmin", "branch_staff", "admin_staff",  "teacher", "ceo","cfo","coo","hr","cmo", "mentor")
    exclude = ("is_active",)
    template_name = "masters/pdfbook/object_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        if user.usertype == "teacher":
            try:
                teacher = Employee.objects.get(user=user)
                form.fields["course"].queryset = Course.objects.filter(id=teacher.course.id)
                form.initial["course"] = teacher.course 
            except Employee.DoesNotExist:
                form.fields["course"].queryset = Course.objects.none() 

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["pdfbook_formset"] = PdfBookFormSet(self.request.POST, self.request.FILES)
        else:
            context["pdfbook_formset"] = PdfBookFormSet()
        context["title"] = "Create PDF Book"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        pdfbook_formset = PdfBookFormSet(self.request.POST, self.request.FILES)

        with transaction.atomic():
            self.object = form.save()
            pdfbook_formset.instance = self.object

            if pdfbook_formset.is_valid():
                pdfbook_formset.save()
            else:
                print("\nFormset Errors:")
                for form in pdfbook_formset:
                    if form.errors:
                        print(form.errors.as_json())
                print("\nNon-Form Errors:", pdfbook_formset.non_form_errors())
                return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        return render(self.request, self.template_name, context)


class PDFBookResourceUpdateView(mixins.HybridUpdateView):
    model = PDFBookResource
    permissions = ("superadmin", "branch_staff", "admin_staff",  "teacher", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "masters/pdfbook/object_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pdfbook_instance = self.get_object() 

        formset_queryset = PdfBook.objects.filter(resource=pdfbook_instance, is_active=True)

        if self.request.POST:
            context['pdfbook_formset'] = PdfBookFormSet(self.request.POST, self.request.FILES, instance=pdfbook_instance, queryset=formset_queryset)
        else:
            context['pdfbook_formset'] = PdfBookFormSet(instance=pdfbook_instance, queryset=formset_queryset)

        context["title"] = "Update PDF Book"
        context["is_pdfbook"] = True
        return context
   
    def form_valid(self, form):
        
        self.object = form.save()
        
        pdfbook_formset = PdfBookFormSet(self.request.POST, self.request.FILES, instance=self.object)
        
        pdfbook_formset.instance = self.object

        if pdfbook_formset.is_valid():
            PdfBook.objects.filter(resource=self.object).delete()
            for f in pdfbook_formset:
                f.instance.resource = self.object
                f.save()
                print('create')
            # pdfbook_formset.save()
            return super().form_valid(form)
        else:
            print("\nFormset Errors:")
            for form in pdfbook_formset:
                if form.errors:
                    print(form.errors.as_json())
            print("\nNon-Form Errors:", pdfbook_formset.non_form_errors())

            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        return render(self.request, self.template_name, context)
    

class PDFBookResourceDeleteView(mixins.HybridDeleteView):
    model = PDFBookResource
    permissions = ("superadmin",'branch_staff', "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    

class PDFBookListView(mixins.HybridListView):
    model = PdfBook
    table_class = tables.PdfBookTable
    filterset_fields = ('name',)
    permissions = ("superadmin", "partner", 'branch_staff', "admin_staff", 'teacher', "student", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        user = self.request.user

        if user.usertype == "student":
            student_courses = Admission.objects.filter(user=user).values_list("course", flat=True)
            
            queryset = queryset.filter(resource__course__in=student_courses)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "PDF Book List"
        context["is_pdf_book"] = True
        user = self.request.user
        context["can_add"] = user.usertype == "teacher" and getattr(user, "branch_staff", False)
        context["new_link"] = reverse_lazy("masters:pdfbook_resource_create")
        return context
    

class CourseSyllabusMasterView(mixins.HybridListView):
    model = Course
    table_class = tables.CourseSyllabusMasterTable
    filterset_fields = {'name': ['exact'], }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Course Syllabus Master"
        context["is_course_syllabus_master"] = True
        context["can_add"] = False
        return context

class SyllabusMasterList(mixins.HybridListView):
    model = SyllabusMaster
    table_class = tables.SyllabusMasterTable
    filterset_fields = {'course': ['exact'], 'month': ['exact'], 'week': ['exact']}  
    permissions = ('admin_staff',  "partner", 'is_superuser', 'student', "ceo","cfo","coo","hr","cmo", "mentor",)

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        
        if self.request.user.usertype == "teacher":
            try:
                teacher = Employee.objects.get(user=self.request.user)
                qs = qs.filter(course=teacher.course)
            except Employee.DoesNotExist:
                qs = SyllabusMaster.objects.none()

        if self.request.user.usertype == "student":
            try:
                student = Admission.objects.get(user=self.request.user)
                qs = qs.filter(course=student.course)
            except Admission.DoesNotExist:
                qs = SyllabusMaster.objects.none()
        return qs

    
class SyllabusMasterDetailView(mixins.HybridDetailView):
    model = SyllabusMaster
    permissions = ('admin_staff',  "partner", 'is_superuser', 'student', "ceo","cfo","coo","hr","cmo", "mentor")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Syllabus Master"
        context["is_syllabus_master"] = True
        return context


class SyllabusMasterCreateView(mixins.HybridCreateView):
    model = SyllabusMaster
    template_name = "masters/syllabus/syllabusmaster_form.html"
    form_class = SyllabusMasterForm
    permissions = ('admin_staff', 'is_superuser', "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        syllabus_formset = SyllabusFormSet(instance=self.object if hasattr(self, 'object') else None)

        if self.request.POST:
            context['syllabus_formset'] = SyllabusFormSet(
                self.request.POST,
                instance=self.object if hasattr(self, 'object') else None
            )
        else:
            context['syllabus_formset'] = SyllabusFormSet(
                instance=self.object if hasattr(self, 'object') else None
            )

        for form in syllabus_formset.forms:
            for field in form.fields.values():
                field.label = ""

        context["title"] = "Syllabus Master Create"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        syllabus_formset = context['syllabus_formset']

        self.object = form.save()

        if syllabus_formset.is_valid():
            syllabus_formset.instance = self.object
            syllabus_formset.save()
        else:
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("masters:course_syllabus_list", kwargs={"pk": self.object.course.pk})

    
class SyllabusMasterUpdateView(mixins.HybridUpdateView):
    model = SyllabusMaster
    template_name = "masters/syllabus/syllabusmaster_form.html"
    form_class = SyllabusMasterForm
    permissions = ('admin_staff', 'is_superuser', "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_qs = self.object.syllabus_set.filter(is_active=True)

        if self.request.POST:
            context['syllabus_formset'] = SyllabusFormSet(
                self.request.POST,
                instance=self.object,
                queryset=active_qs
            )
        else:
            context['syllabus_formset'] = SyllabusFormSet(
                instance=self.object,
                queryset=active_qs
            )

        context["title"] = "Syllabus Master Update"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        syllabus_formset = context['syllabus_formset']

        self.object = form.save()

        if syllabus_formset.is_valid():
            for deleted_form in syllabus_formset.deleted_forms:
                instance = deleted_form.instance
                if instance.pk:  
                    instance.is_active = False
                    instance.save()

            syllabus_formset.save()
        else:
            print("Formset errors:", syllabus_formset.errors)
            print("Formset non_form_errors:", syllabus_formset.non_form_errors())
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("masters:course_syllabus_list", kwargs={"pk": self.object.course.pk})

    
class SyllabusMasterDeleteView(mixins.HybridDeleteView):
    model = SyllabusMaster
    permissions = (
        'admin_staff', 'is_superuser',
        "ceo", "cfo", "coo", "hr", "cmo", "mentor"
    )

    def get_success_url(self):
        course_id = self.object.course_id 
        return reverse_lazy(
            "masters:course_syllabus_list",
            kwargs={"pk": course_id}
        )
    

class SyllabusListView(mixins.HybridListView):
    model = Syllabus 
    table_class = tables.SyllabusTable
    filterset_fields = {'syllabus_master': ['exact'], 'title': ['contains'],}  
    permissions = ('admin_staff',  "partner", 'is_superuser', 'student', "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Syllabus"
        context["is_syllabus"] = True
        context['can_add'] = True
        context["new_link"] = reverse_lazy("masters:syllabus_create")
        return context
    
    
    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)

        if self.request.user.usertype == "teacher":
            try:
                teacher = Employee.objects.get(user=self.request.user)
                qs = qs.filter(master=teacher.syllabus_master)
            except Employee.DoesNotExist:
                qs = Syllabus.objects.none()

        if self.request.user.usertype == "student":
            try:
                student = Admission.objects.get(user=self.request.user)
                qs = qs.filter(master=student.syllabus_master)
            except Admission.DoesNotExist:
                qs = Syllabus.objects.none()
        return qs


class SyllabusDetailView(mixins.HybridDetailView):
    model = Syllabus
    permissions = ('admin_staff',  "partner", 'is_superuser', 'student', "ceo","cfo","coo","hr","cmo", "mentor")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Syllabus"
        context["is_syllabus"] = True
        return context

    
class SyllabusCreateView(mixins.HybridCreateView):
    model = Syllabus
    permissions = ('admin_staff', 'is_superuser', "ceo","cfo","coo","hr","cmo", "mentor")
    form_class = forms.SyllabusForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Syllabus Create" 
        return context

    
class SyllabusUpdateView(mixins.HybridUpdateView):
    model = Syllabus
    permissions = ('admin_staff', 'is_superuser', "ceo","cfo","coo","hr","cmo", "teacher", "mentor")
    form_class = forms.SyllabusForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Syllabus Update" 
        return context

    
class SyllabusDeleteView(mixins.HybridDeleteView):
    model = Syllabus
    permissions = ('admin_staff', 'is_superuser', "ceo","cfo","coo","hr","cmo", "mentor")

    def get_success_url(self):
        return reverse_lazy("masters:course_syllabus_list", kwargs={"pk": self.object.syllabus_master.course_id})
    

class CourseSyllabusView(mixins.HybridListView):
    model = Syllabus
    template_name = "masters/syllabus/coursesyllabus_list.html"
    table_class = tables.SyllabusTable
    permissions = ('admin_staff', "mentor",  "partner", 'is_superuser', 'student', "ceo","cfo","coo","hr","cmo", "teacher")

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        usertype = self.request.user.usertype
        course_id = self.kwargs.get("pk")

        if usertype in ["teacher", "student"]:
            if course_id:
                qs = qs.filter(syllabus_master__course_id=course_id, is_active=True)
        elif usertype in ["admin_staff", "ceo", "cfo", "coo", "hr", "cmo"]:
            if course_id:
                qs = qs.filter(syllabus_master__course_id=course_id, is_active=True)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get("pk")
        course = Course.objects.filter(pk=course_id, is_active=True).first()
        context["title"] = f"Syllabus – {course.name}" if course else "Syllabus"
        context["is_course_syllabus"] = True
        context['can_add'] = self.request.user.usertype != "teacher" and self.request.user.usertype != "student"
        context["new_link"] = reverse_lazy("masters:syllabus_master_create")

        syllabus_masters = SyllabusMaster.objects.filter(course_id=course_id, is_active=True)
        user = self.request.user

        for master in syllabus_masters:
            active_syllabus = master.syllabus_set.filter(is_active=True)
            for syllabus in active_syllabus:
                # Only filter by user
                status_obj = BatchSyllabusStatus.objects.filter(
                    syllabus=syllabus,
                    user=user
                ).first()
                syllabus.user_status = status_obj.status if status_obj else 'pending'
            master.active_syllabus = active_syllabus

        context["syllabus_masters"] = syllabus_masters
        return context

    
class SyllabusReportView(mixins.HybridListView):
    model = Syllabus
    template_name = "masters/syllabus/syllabus_report.html"
    table_class = tables.SyllabusTable
    filterset_fields = {'title': ['icontains']}
    permissions = ('admin_staff', 'is_superuser', 'student', "ceo","cfo","coo","hr","cmo", "mentor")

    def get_queryset(self):
        queryset = super().get_queryset()
        master_id = self.kwargs.get("pk")
        if master_id:
            queryset = queryset.filter(syllabus_master_id=master_id)
        # Prefetch statuses and related user/batch
        queryset = queryset.prefetch_related(
            'batchsyllabusstatus_set__batch',
            'batchsyllabusstatus_set__user',
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        syllabus_list = []
        status_choices = BatchSyllabusStatus.SYLLABUS_STATUS_CHOICES
        context["can_add"] = False

        # For AJAX requests, we'll return minimal data
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return only basic syllabus info for initial rendering
            for syllabus in context["table"].data:
                course = syllabus.syllabus_master.course
                syllabus_list.append({
                    "id": syllabus.id,
                    "order_id": syllabus.order_id,
                    "title": syllabus.title,
                    "course": course,
                })
            context["table"] = {"data": syllabus_list}
            return context

        # Collect all unique branches and batches for global filter
        all_branches_set = set()
        all_batches_set = set()

        for syllabus in context["table"].data:
            statuses = BatchSyllabusStatus.objects.filter(
                syllabus=syllabus
            ).select_related("batch", "user")

            completed_students, pending_students = [], []
            completed_batches, pending_batches = [], []

            # --- COURSE from syllabus master ---
            course = syllabus.syllabus_master.course

            # --- STUDENTS ---
            all_batches = Batch.objects.filter(course=course)
            all_students = Admission.objects.filter(
                batch__in=all_batches,
                course=course,
                is_active=True,
            ).select_related("user", "batch", "course")

            for student in all_students:
                if not student.user:  # skip admissions without user
                    continue

                # Add to global branches and batches
                if student.user.branch and student.user.branch.is_active:
                    all_branches_set.add(student.user.branch)
                if student.batch:
                    all_batches_set.add(student.batch)

                status_obj = statuses.filter(user=student.user, batch=student.batch).first()
                if status_obj and status_obj.status == "completed":
                    completed_students.append({
                        "syllabus": syllabus,
                        "batch": student.batch,
                        "user": student.user,
                        "course": student.course,
                        "status": "completed"
                    })
                else:
                    pending_students.append({
                        "syllabus": syllabus,
                        "batch": student.batch,
                        "user": student.user,
                        "course": student.course,
                        "status": "pending"
                    })

            # --- BATCHES ---
            for batch in all_batches:
                # Get all students in this batch
                batch_students = Admission.objects.filter(
                    batch=batch,
                    course=course,
                    is_active=True,
                ).select_related("user").count()

                if batch_students == 0:
                    continue  # Skip batches with no students

                # Get completed students count for this batch
                completed_count = statuses.filter(
                    batch=batch,
                    status="completed"
                ).count()

                # Get pending students count for this batch
                pending_count = batch_students - completed_count

                # Calculate completion percentage
                completion_percentage = (completed_count / batch_students * 100) if batch_students > 0 else 0

                batch_data = {
                    "batch": batch,
                    "batch_name": batch.batch_name,
                    "branch": batch.branch,
                    "total_students": batch_students,
                    "completed_students": completed_count,
                    "pending_students": pending_count,
                    "completion_percentage": round(completion_percentage, 1),
                }

                # Determine if batch is completed or pending
                if completion_percentage == 100:
                    completed_batches.append(batch_data)
                else:
                    pending_batches.append(batch_data)

            # --- BRANCHES & BATCHES for filtering ---
            all_users = [
                s["user"] for s in completed_students + pending_students
                if s["user"]
            ]

            branches = sorted(
                {u.branch for u in all_users if hasattr(u, "branch") and u.branch and u.branch.is_active},
                key=lambda b: b.name
            )

            batches = sorted(
                {
                    s["batch"] for s in completed_students + pending_students
                    if s["batch"]
                },
                key=lambda b: b.id
            )

            syllabus_list.append({
                "id": syllabus.id,
                "order_id": syllabus.order_id,
                "title": syllabus.title,
                "course": course,
                "completed_students": completed_students,
                "pending_students": pending_students,
                "completed_batches": completed_batches,
                "pending_batches": pending_batches,
                "branches": branches,
                "batches": batches,
                "status_choices": status_choices,
            })

        # Add global filter data to context
        context["all_branches"] = sorted(all_branches_set, key=lambda b: b.name)
        context["all_batches"] = sorted(all_batches_set, key=lambda b: b.batch_name)
        context["table"] = {"data": syllabus_list}
        return context

    def get_syllabus_details(self, syllabus_id):
        """AJAX endpoint to get syllabus details when accordion is opened"""
        try:
            syllabus = Syllabus.objects.prefetch_related(
                'batchsyllabusstatus_set__batch',
                'batchsyllabusstatus_set__user',
            ).get(id=syllabus_id)
            
            statuses = BatchSyllabusStatus.objects.filter(
                syllabus=syllabus
            ).select_related("batch", "user")

            completed_students, pending_students = [], []
            completed_batches, pending_batches = [], []

            # --- COURSE from syllabus master ---
            course = syllabus.syllabus_master.course

            # --- STUDENTS ---
            all_batches = Batch.objects.filter(course=course)
            all_students = Admission.objects.filter(
                batch__in=all_batches,
                course=course,
                is_active=True,
            ).select_related("user", "batch", "course").prefetch_related("user__branch")

            for student in all_students:
                status_obj = statuses.filter(user=student.user, batch=student.batch).first()
                if status_obj and status_obj.status == "completed":
                    completed_students.append({
                        "batch": {
                            "id": student.batch.id,
                            "batch_name": student.batch.batch_name
                        } if student.batch else None,
                        "user": {
                            "id": student.user.id,
                            "first_name": student.user.first_name,
                            "last_name": student.user.last_name,
                            "full_name": student.user.get_full_name(),
                            "branch": {
                                "id": student.user.branch.id,
                                "name": student.user.branch.name
                            } if student.user and student.user.branch else None
                        } if student.user else {
                            "id": None,
                            "first_name": "Unknown",
                            "last_name": "Student",
                            "full_name": "Unknown Student",
                            "branch": None
                        },
                        "course": student.course.name if student.course else "",
                        "admission_number": student.admission_number,
                        "status": "completed"
                    })
                else:
                    pending_students.append({
                        "batch": {
                            "id": student.batch.id,
                            "batch_name": student.batch.batch_name
                        } if student.batch else None,
                        "user": {
                            "id": student.user.id,
                            "first_name": student.user.first_name,
                            "last_name": student.user.last_name,
                            "full_name": student.user.get_full_name(),
                            "branch": {
                                "id": student.user.branch.id,
                                "name": student.user.branch.name
                            } if student.user and student.user.branch else None
                        } if student.user else {
                            "id": None,
                            "first_name": "Unknown",
                            "last_name": "Student",
                            "full_name": "Unknown Student",
                            "branch": None
                        },
                        "course": student.course.name if student.course else "",
                        "admission_number": student.admission_number,
                        "status": "pending"
                    })

            # --- BATCHES ---
            for batch in all_batches:
                # Get all students in this batch
                batch_students = Admission.objects.filter(
                    batch=batch,
                    course=course,
                    is_active=True,
                ).select_related("user").count()

                if batch_students == 0:
                    continue  # Skip batches with no students

                # Get completed students count for this batch
                completed_count = statuses.filter(
                    batch=batch,
                    status="completed"
                ).count()

                # Get pending students count for this batch
                pending_count = batch_students - completed_count

                # Calculate completion percentage
                completion_percentage = (completed_count / batch_students * 100) if batch_students > 0 else 0

                batch_data = {
                    "batch": {
                        "id": batch.id,
                        "batch_name": batch.batch_name
                    },
                    "branch": {
                        "id": batch.branch.id,
                        "name": batch.branch.name
                    } if batch.branch else None,
                    "total_students": batch_students,
                    "completed_students": completed_count,
                    "pending_students": pending_count,
                    "completion_percentage": round(completion_percentage, 1),
                }

                # Determine if batch is completed or pending
                if completion_percentage == 100:
                    completed_batches.append(batch_data)
                else:
                    pending_batches.append(batch_data)

            return {
                "id": syllabus.id,
                "completed_students": completed_students,
                "pending_students": pending_students,
                "completed_batches": completed_batches,
                "pending_batches": pending_batches,
            }
        except Syllabus.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        # Handle AJAX request for syllabus details
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('action') == 'get_syllabus_details':
            syllabus_id = request.GET.get('syllabus_id')
            if syllabus_id:
                details = self.get_syllabus_details(syllabus_id)
                if details:
                    return JsonResponse(details)
                else:
                    return JsonResponse({'error': 'Syllabus not found'}, status=404)
        return super().dispatch(request, *args, **kwargs)


class BatchSyllabusReportView(mixins.HybridListView):
    model = Syllabus
    template_name = "masters/syllabus/batch_syllabus_report.html"
    permissions = ('teacher', 'admin_staff', 'is_superuser', "ceo","cfo","coo","hr","cmo", "mentor")

    def get_queryset(self):
        queryset = super().get_queryset()
        master_id = self.kwargs.get("pk")
        if master_id:
            queryset = queryset.filter(syllabus_master_id=master_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        master_id = self.kwargs.get("pk")
        batch_id = self.request.GET.get('batch')

        # Get batches for teacher
        if self.request.user.usertype == 'teacher':
            # Get employee record
            try:
                employee = Employee.objects.get(user=self.request.user)
                batches = Batch.objects.filter(
                    branch=employee.branch,
                    course=employee.course,
                    is_active=True,
                    status='in_progress'
                )
            except Employee.DoesNotExist:
                batches = Batch.objects.none()
        else:
            batches = Batch.objects.filter(is_active=True, status='in_progress')

        # Get syllabus data
        syllabus_data = []
        completed_syllabus = []
        pending_syllabus = []

        if batch_id:
            try:
                batch = Batch.objects.get(id=batch_id, status='in_progress')
                syllabus_data = self.get_syllabus_batch_status(master_id, batch_id)

                for syllabus in syllabus_data:
                    if syllabus['teacher_status'] == 'completed':
                        completed_syllabus.append(syllabus)
                    else:
                        pending_syllabus.append(syllabus)

            except Batch.DoesNotExist:
                pass

        # Calculate progress percentage
        total_count = len(completed_syllabus) + len(pending_syllabus)
        progress_percentage = 0
        if total_count > 0:
            progress_percentage = round((len(completed_syllabus) / total_count) * 100)

        context.update({
            "batches": batches,
            "selected_batch": batch_id,
            "completed_syllabus": completed_syllabus,
            "pending_syllabus": pending_syllabus,
            "completed_count": len(completed_syllabus),
            "pending_count": len(pending_syllabus),
            "total_count": total_count,
            "progress_percentage": progress_percentage,
            "syllabus_master_id": master_id,
        })

        return context
    
    def get_syllabus_batch_status(self, master_id, batch_id):
        """Get syllabus status for batch"""
        syllabuses = Syllabus.objects.filter(
            syllabus_master_id=master_id
        ).order_by('order_id')

        # Get teacher status for all syllabuses in one query
        teacher_statuses = BatchSyllabusStatus.objects.filter(
            syllabus__in=syllabuses,
            user=self.request.user,
            batch_id=batch_id
        ).values('syllabus_id', 'status')
        
        teacher_status_dict = {status['syllabus_id']: status['status'] for status in teacher_statuses}

        syllabus_list = []
        for syllabus in syllabuses:
            teacher_status = teacher_status_dict.get(syllabus.id, 'pending')
            
            syllabus_list.append({
                "id": syllabus.id,
                "order_id": syllabus.order_id,
                "title": syllabus.title,
                "description": syllabus.description,
                "teacher_status": teacher_status,
            })
        
        return syllabus_list
    
    
class StudentSyllabusReportView(TemplateView):
    template_name = "masters/syllabus/student_syllabus_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Get the Admission record (not User) using the PK from the URL
        # Your URL uses <int:pk>, so we fetch using that ID.
        admission_id = self.kwargs.get('pk')
        admission = get_object_or_404(Admission, id=admission_id)
        
        # Extract related data from the admission record
        student_user = admission.user
        student_batch = admission.batch
        student_course = admission.course

        # 2. Get all Syllabus topics for this specific course
        # We MUST order by syllabus_master__order_id first for groupby to work correctly
        syllabuses = Syllabus.objects.filter(
            syllabus_master__course=student_course
        ).select_related('syllabus_master').order_by(
            'syllabus_master__order_id', 
            'order_id'
        )
        
        # 3. Get the status for each syllabus for THIS student in THIS batch
        # We create a dictionary for O(1) lookup: {syllabus_id: status}
        user_statuses = BatchSyllabusStatus.objects.filter(
            user=student_user, 
            batch=student_batch
        ).values('syllabus_id', 'status')
        status_map = {item['syllabus_id']: item['status'] for item in user_statuses}

        # 4. Prepare data for grouping
        processed_list = []
        completed_count = 0
        
        for syl in syllabuses:
            current_status = status_map.get(syl.id, 'pending')
            if current_status == 'completed':
                completed_count += 1
            
            processed_list.append({
                'master_obj': syl.syllabus_master,  # This is the object we group by
                'id': syl.id,
                'title': syl.title,
                'status': current_status,
                'description': syl.description,
                'homework': syl.homework,
            })

        # 5. Group the list by SyllabusMaster
        # groupby requires the list to be pre-sorted by the same key (done in step 2)
        grouped_syllabus = []
        for master, items in groupby(processed_list, key=lambda x: x['master_obj']):
            grouped_syllabus.append({
                'master': master,
                'topics': list(items)
            })

        # 6. Calculate Metrics
        total_topics = len(processed_list)
        pending_count = total_topics - completed_count
        percentage = int((completed_count / total_topics * 100)) if total_topics > 0 else 0

        # 7. Update Context
        context.update({
            "title": f"Report: {admission.fullname()}",
            "student": admission,  # In template, we can access student.fullname, student.course, etc.
            "grouped_syllabus": grouped_syllabus,
            "metrics": {
                "total": total_topics,
                "completed": completed_count,
                "pending": pending_count,
                "percentage": percentage
            }
        })
        return context


class ComplaintListView(mixins.HybridListView):
    model = ComplaintRegistration
    table_class = tables.ComplaintTable
    filterset_fields = {'complaint_type': ['exact'],}  
    permissions = ("admin_staff", "is_superuser", "student","ceo","cfo","coo","hr","cmo", "mentor")
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        user = self.request.user
        if user.usertype == "student":
            queryset = queryset.filter(creator=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Complaint"
        context['is_master'] = True
        context["is_complaint"] = True
        user_type = self.request.user.usertype
        context["can_add"] = user_type not in ("teacher", "admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo")
        context["new_link"] = reverse_lazy("masters:complaint_create")
        return context
    

class ComplaintDetailView(mixins.HybridDetailView):
    model = ComplaintRegistration
    permissions = ("admin_staff", "branch_staff", "teacher", "student", "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Complaint"
        return context
    

class ComplaintCreateView(mixins.HybridCreateView):
    model = ComplaintRegistration
    permissions = ("admin_staff", "branch_staff", "teacher", "student", "ceo", "cfo", "coo", "hr", "cmo", "mentor")
    form_class = forms.ComplaintForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Complaint"
        return context

    def get_success_url(self):
        return reverse_lazy("masters:complaint_detail", kwargs={"pk": self.object.pk})


class ComplaintUpdateView(mixins.HybridUpdateView):
    model = ComplaintRegistration
    permissions = ("admin_staff", "branch_staff", "teacher","ceo","cfo","coo","hr","cmo", "mentor")
    form_class = forms.ComplaintForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Complaint"
        return context
    

class ComplaintDeleteView(mixins.HybridDeleteView):
    model = ComplaintRegistration
    permissions = ("admin_staff", "branch_staff", "teacher","ceo","cfo","coo","hr","cmo", "mentor")



class ChatListView(mixins.HybridListView):
    """Chat List Page — perfectly synced with StudentChatView"""
    template_name = "masters/chat/student_chat_list.html"
    model = Admission
    table_class = tables.ChatSessionTable
    permissions = (
        "admin_staff", "branch_staff", "teacher", "is_superuser",
        "student", "mentor", "ceo", "cfo", "coo", "hr", "cmo"
    )
    paginate_by = None
    filterset_fields = {"batch": ["exact"], "branch": ["exact"], "course": ["exact"]}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # IMPORTANT: Override object_list with our sorted annotated data
        context['object_list'] = self.get_table_data()
        
        context.update({
            "title": "Messages",
            "is_chat_session": True,
            "can_add": False,
            "current_user": self.request.user,
            "paginate_by": None,
        })
        return context

    # --------------------------------------------------------------------
    def get_queryset(self):
        """Get all users visible to the current user"""
        current_user = self.request.user
        queryset = super().get_queryset()

        if current_user.usertype == "mentor":
            try:
                employee = Employee.objects.get(user=current_user)
                # Show ALL students in mentor's branch (even without chat history)
                queryset = queryset.filter(
                    is_active=True,
                    user__is_active=True,
                    user__usertype="student",
                    branch=employee.branch
                )
            except Employee.DoesNotExist:
                queryset = queryset.none()

        elif current_user.usertype == "branch_staff":
            # Show ALL active students in branch
            queryset = queryset.filter(is_active=True, branch=current_user.branch)

        elif current_user.usertype == "teacher":
            try:
                employee = Employee.objects.get(user=current_user)
                # Show ALL students in teacher's branch and course
                queryset = queryset.filter(
                    is_active=True,
                    branch=employee.branch,
                    course=employee.course,
                    user__usertype="student"
                )
            except Employee.DoesNotExist:
                queryset = queryset.none()

        elif current_user.usertype == "student":
            # Students only see people they have chatted with
            sent_to = ChatSession.objects.filter(sender=current_user).values_list("recipient_id", flat=True)
            received_from = ChatSession.objects.filter(recipient=current_user).values_list("sender_id", flat=True)
            chat_user_ids = set(list(sent_to) + list(received_from))
            queryset = queryset.filter(user_id__in=chat_user_ids)

        else:
            # Other user types only see people they've chatted with
            sent_to = ChatSession.objects.filter(sender=current_user).values_list("recipient_id", flat=True)
            received_from = ChatSession.objects.filter(recipient=current_user).values_list("sender_id", flat=True)
            chat_user_ids = set(list(sent_to) + list(received_from))
            queryset = queryset.filter(user_id__in=chat_user_ids)

        return queryset.distinct()

    # --------------------------------------------------------------------
    def get_table_data(self):
        """
        Build chat list data exactly like StudentChatView.annotate_chat_users_compatible()
        Ensures the same order and message preview.
        """
        current_user = self.request.user
        chat_users = self.get_queryset()
        annotated_users = []

        for student in chat_users:
            # Get all messages with this user
            all_messages = ChatSession.objects.filter(
                Q(sender=student.user, recipient=current_user) |
                Q(sender=current_user, recipient=student.user)
            ).order_by('-created')
            
            # Find last non-deleted message
            last_msg = None
            for msg in all_messages:
                if current_user.id not in msg.deleted_by_ids:
                    last_msg = msg
                    break
            
            # Skip ONLY if there ARE messages but ALL are deleted
            # If no messages at all, we KEEP the user (don't skip)
            if all_messages.exists() and not last_msg:
                # All messages are deleted, skip this user
                continue
            
            # Count unread non-deleted messages
            unread_msgs = ChatSession.objects.filter(
                sender=student.user,
                recipient=current_user,
                read=False
            )
            unread_count = sum(1 for msg in unread_msgs if current_user.id not in msg.deleted_by_ids)
            
            # Add attributes
            student.last_message_time = last_msg.created if last_msg else None
            
            # Handle message text and attachment
            if last_msg:
                if last_msg.message:
                    student.last_message_text = last_msg.message
                elif last_msg.attachment:
                    # Get file name and determine type
                    file_name = last_msg.attachment.name.split("/")[-1].lower()
                    if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        student.last_message_text = "📷 Photo"
                    elif '.pdf' in file_name:
                        student.last_message_text = "📄 PDF Document"
                    elif any(ext in file_name for ext in ['.mp4', '.mov', '.avi']):
                        student.last_message_text = "🎬 Video"
                    elif any(ext in file_name for ext in ['.doc', '.docx']):
                        student.last_message_text = "📝 Document"
                    elif any(ext in file_name for ext in ['.xls', '.xlsx']):
                        student.last_message_text = "📊 Spreadsheet"
                    else:
                        student.last_message_text = f"📎 {file_name}"
                else:
                    student.last_message_text = "No messages yet"
            else:
                # No messages at all with this user
                student.last_message_text = "No messages yet"
            
            student.last_message_sender_id = last_msg.sender_id if last_msg else None
            student.unread_count = unread_count
            
            annotated_users.append(student)
        
        # Sort by last message time (LATEST ON TOP)
        # Users with no messages will appear at the bottom
        annotated_users.sort(
            key=lambda x: x.last_message_time if x.last_message_time else timezone.datetime.min.replace(tzinfo=timezone.get_current_timezone()),
            reverse=True
        )
        
        return annotated_users


class StudentChatView(TemplateView):
    template_name = "masters/chat/student_chat_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_user = get_object_or_404(User, id=self.kwargs["user_id"])
        current_user = self.request.user

        # Validate access permissions for teachers
        if current_user.usertype == "teacher":
            try:
                employee = Employee.objects.get(user=current_user)
                # Check if other_user is a student from teacher's branch and course
                try:
                    other_admission = Admission.objects.get(
                        user=other_user,
                        branch=employee.branch,
                        course=employee.course,
                        is_active=True
                    )
                except Admission.DoesNotExist:
                    # Teacher trying to access student outside their branch/course
                    from django.contrib import messages
                    messages.error(self.request, "You don't have permission to chat with this user.")
                    return redirect("masters:chat_list")
            except Employee.DoesNotExist:
                from django.contrib import messages
                messages.error(self.request, "Employee profile not found.")
                return redirect("masters:chat_list")

        # Get messages WITHOUT exclude (we'll filter in Python)
        all_chat_messages = ChatSession.objects.filter(
            Q(sender=current_user, recipient=other_user) |
            Q(sender=other_user, recipient=current_user)
        ).select_related('sender', 'recipient').order_by("-created")

        # Filter out deleted messages in Python and get last 20
        chat_messages = [
            msg for msg in all_chat_messages[:50]  # Get extra to ensure 20 after filtering
            if current_user.id not in msg.deleted_by_ids
        ][:20]

        chat_messages = list(reversed(chat_messages))

        # Mark unread messages as read (filter in Python)
        unread_messages = ChatSession.objects.filter(
            sender=other_user,
            recipient=current_user,
            read=False
        )
        for msg in unread_messages:
            if current_user.id not in msg.deleted_by_ids:
                msg.read = True
                msg.read_at = timezone.now()
                msg.save(update_fields=['read', 'read_at'])

        # Get chat users list
        chat_users = self.get_chat_users(current_user)

        # Annotate chat data
        chat_users = self.annotate_chat_users_compatible(chat_users, current_user)

        # Avatar URLs
        context.update(self.get_avatar_urls(current_user, other_user))

        # Other user's admission info
        try:
            context["other_admission"] = Admission.objects.get(user=other_user)
        except Admission.DoesNotExist:
            context["other_admission"] = None

        # Preserve filter parameters for back link
        context["back_url"] = self.get_back_url()

        # Get total message count (filter in Python)
        all_messages = ChatSession.objects.filter(
            Q(sender=current_user, recipient=other_user) |
            Q(sender=other_user, recipient=current_user)
        )
        total_messages = sum(1 for msg in all_messages if current_user.id not in msg.deleted_by_ids)

        # Final context
        context.update({
            "messages": chat_messages,
            "other_user": other_user,
            "current_user": current_user,
            "chat_users": chat_users,
            "title": f"Chat with {other_user.get_full_name()}",
            "total_messages": total_messages
        })

        return context

    def get_back_url(self):
        """Generate back URL with preserved filter parameters"""
        base_url = reverse_lazy('masters:chat_list')
        filter_params = []
        
        # Preserve these filter parameters
        for param in ['batch', 'branch', 'course']:
            value = self.request.GET.get(param)
            if value:
                filter_params.append(f"{param}={value}")
        
        if filter_params:
            return f"{base_url}?{'&'.join(filter_params)}"
        return base_url

    def get_chat_users(self, current_user):
        """Get chat users based on user role"""
        if current_user.usertype == "mentor":
            try:
                employee = Employee.objects.get(user=current_user)
                return Admission.objects.filter(
                    is_active=True,
                    user__is_active=True,
                    branch=employee.branch
                )
            except Employee.DoesNotExist:
                return Admission.objects.none()

        elif current_user.usertype == "branch_staff":
            return Admission.objects.filter(
                is_active=True,
                user__is_active=True,
                branch=current_user.branch
            )

        elif current_user.usertype == "teacher":
            # ONLY show students from teacher's branch and course
            try:
                employee = Employee.objects.get(user=current_user)
                return Admission.objects.filter(
                    is_active=True,
                    user__is_active=True,
                    branch=employee.branch,
                    course=employee.course,
                    user__usertype="student"
                )
            except Employee.DoesNotExist:
                return Admission.objects.none()

        else:
            # student and any other roles: only show active admissions they've chatted with
            sent_to = ChatSession.objects.filter(sender=current_user).values_list("recipient_id", flat=True)
            received_from = ChatSession.objects.filter(recipient=current_user).values_list("sender_id", flat=True)
            chat_user_ids = set(sent_to) | set(received_from)

            return Admission.objects.filter(
                user_id__in=chat_user_ids,
                is_active=True,
                user__is_active=True
            ).distinct()

    def annotate_chat_users_compatible(self, chat_users, current_user):
        """Annotate chat users - compatible with all databases - SORTED BY LATEST MESSAGE"""
        annotated_users = []
        
        for student in chat_users:
            # Get all messages with this user
            all_messages = ChatSession.objects.filter(
                Q(sender=student.user, recipient=current_user) |
                Q(sender=current_user, recipient=student.user)
            ).order_by('-created')
            
            # Find last non-deleted message
            last_msg = None
            for msg in all_messages:
                if current_user.id not in msg.deleted_by_ids:
                    last_msg = msg
                    break
            
            # Skip if no non-deleted messages
            if not last_msg and all_messages.exists():
                # Check if all messages are deleted
                has_any_message = False
                for msg in all_messages:
                    if current_user.id not in msg.deleted_by_ids:
                        has_any_message = True
                        break
                if not has_any_message:
                    continue  # Skip this user
            
            # Count unread non-deleted messages
            unread_msgs = ChatSession.objects.filter(
                sender=student.user,
                recipient=current_user,
                read=False
            )
            unread_count = sum(1 for msg in unread_msgs if current_user.id not in msg.deleted_by_ids)
            
            # Add attributes
            student.last_message_time = last_msg.created if last_msg else None
            student.last_message_text = last_msg.message if last_msg else None
            student.last_message_sender_id = last_msg.sender_id if last_msg else None
            student.unread_count = unread_count
            
            annotated_users.append(student)
        
        # Sort by last message time (LATEST ON TOP)
        annotated_users.sort(
            key=lambda x: x.last_message_time if x.last_message_time else timezone.datetime.min.replace(tzinfo=timezone.get_current_timezone()),
            reverse=True
        )
        
        return annotated_users

    def get_avatar_urls(self, current_user, other_user):
        """Get avatar URLs for users"""
        return {
            "default_user_avatar": (
                current_user.profile_image.url
                if getattr(current_user, "profile_image", None)
                else f"https://ui-avatars.com/api/?name={current_user.get_full_name()}&background=667eea&color=fff&size=128&bold=true"
            ),
            "other_user_avatar": (
                other_user.profile_image.url
                if getattr(other_user, "profile_image", None)
                else f"https://ui-avatars.com/api/?name={other_user.get_full_name()}&background=764ba2&color=fff&size=128&bold=true"
            )
        }

    def post(self, request, *args, **kwargs):
        other_user = get_object_or_404(User, id=self.kwargs["user_id"])
        current_user = request.user

        if current_user.usertype == "teacher":
            try:
                employee = Employee.objects.get(user=current_user)
                if not Admission.objects.filter(
                    user=other_user,
                    branch=employee.branch,
                    course=employee.course,
                    is_active=True
                ).exists():
                    messages.error(request, "You don't have permission to send messages to this user.")
                    return redirect("masters:chat_list")
            except Employee.DoesNotExist:
                messages.error(request, "Employee profile not found.")
                return redirect("masters:chat_list")

        message_text = request.POST.get("message", "").strip()
        attachment = request.FILES.get("attachment")

        # Validate file size
        if attachment and attachment.size > 1024 * 1024:
            messages.error(request, "File size should not exceed 1 MB.")
            return redirect("masters:student_chat", user_id=other_user.id)

        # Must have message or file
        if not message_text and not attachment:
            messages.warning(request, "Please enter a message or attach a file.")
            return redirect("masters:student_chat", user_id=other_user.id)

        # Save chat
        try:
            ChatSession.objects.create(
                sender=request.user,
                recipient=other_user,
                message=message_text or "",
                attachment=attachment,
                read=False
            )
        except Exception as e:
            messages.error(request, f"Failed to send message: {str(e)}")

        return redirect("masters:student_chat", user_id=other_user.id)


@login_required
def load_more_messages(request):
    other_user_id = request.GET.get('other_user_id')
    offset = int(request.GET.get('offset', 20))
    limit = 20
    
    other_user = get_object_or_404(User, id=other_user_id)
    current_user = request.user
    
    # Get messages - EXCLUDE deleted messages
    messages = ChatSession.objects.filter(
        Q(sender=current_user, recipient=other_user) |
        Q(sender=other_user, recipient=current_user)
    ).exclude(
        deleted_by_ids__contains=current_user.id  # ✅ EXCLUDE DELETED MESSAGES
    ).select_related('sender', 'recipient').order_by('-created')[offset:offset+limit]
    
    messages_data = []
    for message in reversed(messages):
        messages_data.append({
            'id': message.id,
            'message': message.message,
            'attachment_url': message.attachment.url if message.attachment else None,
            'attachment_name': message.attachment.name if message.attachment else None,
            'time': message.created.strftime('%I:%M %p'),
            'is_sent': message.sender == current_user,
            'is_read': message.read,
        })
    
    # Total messages count - EXCLUDE deleted
    total_messages = ChatSession.objects.filter(
        Q(sender=current_user, recipient=other_user) |
        Q(sender=other_user, recipient=current_user)
    ).exclude(
        deleted_by_ids__contains=current_user.id  
    ).count()
    
    return JsonResponse({
        'messages': messages_data,
        'offset': offset + limit,
        'has_more': (offset + limit) < total_messages
    })


class EmployeeChatListView(mixins.HybridListView):
    """Employee Chat List View - Shows conversations with teachers/mentors"""
    template_name = "masters/chat/employee_chat_list.html"
    model = Employee
    table_class = tables.EmployeeChatSessionTable
    filterset_fields = {"branch": ['exact'], 'course': ['exact']}
    permissions = (
        "admin_staff", "branch_staff", "teacher", "is_superuser", 
        "student", "mentor", "ceo", "cfo", "coo", "hr", "cmo"
    )
    paginate_by = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Messages"
        context["is_mentor_chat_session"] = True
        context["can_add"] = False
        context["current_user"] = self.request.user
        
        context["object_list"] = self.get_table_data()
        
        return context

    def get_potential_chat_users(self):
        """
        Get list of User IDs that current user can chat with
        Returns a queryset of User objects
        """
        current_user = self.request.user
        
        if current_user.usertype == "student":
            # Students can chat with ALL mentors and teachers in their branch/course
            admission = Admission.objects.filter(user=current_user, is_active=True).first()
            if admission and admission.branch:
                
                # Get ALL mentors
                mentor_ids = Employee.objects.filter(
                    user__usertype="mentor",
                    is_active=True
                ).values_list('user_id', flat=True)
                
                # Get teachers in same branch/course
                teacher_ids = Employee.objects.filter(
                    user__usertype="teacher",
                    branch=admission.branch,
                    course=admission.course,
                    is_active=True
                ).values_list('user_id', flat=True)
                
                # Combine all user IDs
                all_user_ids = list(mentor_ids) + list(teacher_ids)
                
                return User.objects.filter(id__in=all_user_ids)
            else:
                return User.objects.none()

        elif current_user.usertype == "teacher":
            # Teachers can chat with students in their course/branch
            teacher_emp = Employee.objects.filter(user=current_user).first()
            if teacher_emp and teacher_emp.branch:
                # Get students from same branch and course
                student_user_ids = Admission.objects.filter(
                    branch=teacher_emp.branch,
                    course=teacher_emp.course,
                    is_active=True
                ).values_list("user_id", flat=True)
                
                return User.objects.filter(id__in=student_user_ids)
            else:
                return User.objects.none()

        elif current_user.usertype == "mentor":
            # Mentors can chat with ALL students
            student_user_ids = Admission.objects.filter(
                is_active=True
            ).values_list("user_id", flat=True)
            
            return User.objects.filter(id__in=student_user_ids)

        elif current_user.usertype in ["hr", "branch_staff"]:
            # HR/Branch staff can chat with students in their branch
            student_user_ids = Admission.objects.filter(
                branch=current_user.branch,
                is_active=True
            ).values_list("user_id", flat=True)
            
            return User.objects.filter(id__in=student_user_ids)

        else:
            # Admin/CEO/CFO/COO can see teachers and mentors
            employee_user_ids = Employee.objects.filter(
                user__usertype__in=["teacher", "mentor", "hr"],
                branch=current_user.branch,
                is_active=True
            ).values_list('user_id', flat=True)
            
            return User.objects.filter(id__in=employee_user_ids)

    def get_queryset(self):
        """Keep for compatibility with parent class"""
        return Employee.objects.filter(is_active=True)

    def get_table_data(self):
        """
        Get ALL potential chat users with metadata (shows users even without messages)
        """
        potential_users = self.get_potential_chat_users()
        current_user = self.request.user
        
        annotated_results = []
        
        for user_obj in potential_users:
            # Get all messages with this user
            all_messages = ChatSession.objects.filter(
                Q(sender=user_obj, recipient=current_user) |
                Q(sender=current_user, recipient=user_obj)
            ).order_by('-created')
            
            # Filter out deleted messages and find last visible message
            last_message = None
            for msg in all_messages:
                if current_user.id not in msg.deleted_by_ids:
                    last_message = msg
                    break
            
            # Count unread non-deleted messages
            unread_count = 0
            if all_messages.exists():
                unread_messages = ChatSession.objects.filter(
                    sender=user_obj,
                    recipient=current_user,
                    read=False
                )
                unread_count = sum(
                    1 for msg in unread_messages 
                    if current_user.id not in msg.deleted_by_ids
                )
            
            # Create a simple object to hold user data
            class ChatUserData:
                def __init__(self, user):
                    self.user = user
                    self.last_message_time = None
                    self.last_message_text = None
                    self.last_message_sender_id = None
                    self.unread_count = 0
            
            chat_user = ChatUserData(user_obj)
            
            # ✅ Set data (works even if no messages)
            if last_message:
                chat_user.last_message_time = last_message.created
                chat_user.last_message_text = last_message.message or "[Attachment]"
                chat_user.last_message_sender_id = last_message.sender_id
            else:
                # ✅ No messages - set defaults but STILL SHOW the user
                chat_user.last_message_time = None
                chat_user.last_message_text = ""  # Empty so template shows "No messages yet"
                chat_user.last_message_sender_id = None
            
            chat_user.unread_count = unread_count
            
            annotated_results.append(chat_user)
        
        annotated_results.sort(
            key=lambda x: (
                x.last_message_time is None,  
                -x.last_message_time.timestamp() if x.last_message_time else 0,
                x.user.get_full_name()  
            )
        )
        
        return annotated_results


class ChatView(TemplateView):
    template_name = "masters/chat/object_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_user = get_object_or_404(User, id=self.kwargs["user_id"])
        current_user = self.request.user

        # 🔹 Get messages WITHOUT exclude (we'll filter in Python)
        all_chat_messages = ChatSession.objects.filter(
            Q(sender=current_user, recipient=other_user) |
            Q(sender=other_user, recipient=current_user)
        ).select_related("sender", "recipient").order_by("-created")

        # Filter out deleted messages in Python and get last 20
        chat_messages = [
            msg for msg in all_chat_messages[:50]  # Get extra to ensure 20 after filtering
            if current_user.id not in msg.deleted_by_ids
        ][:20]

        # Reverse for display (oldest first)
        chat_messages = list(reversed(chat_messages))

        # 🔹 Mark unread messages as read (filter in Python)
        unread_messages = ChatSession.objects.filter(
            sender=other_user, 
            recipient=current_user, 
            read=False
        )
        for msg in unread_messages:
            if current_user.id not in msg.deleted_by_ids:
                msg.read = True
                msg.read_at = timezone.now()
                msg.save(update_fields=['read', 'read_at'])

        # Get total message count (filter in Python)
        all_messages = ChatSession.objects.filter(
            Q(sender=current_user, recipient=other_user) |
            Q(sender=other_user, recipient=current_user)
        )
        total_messages = sum(1 for msg in all_messages if current_user.id not in msg.deleted_by_ids)

        # ✅ Get potential chat users (same logic as list view)
        potential_users = self.get_potential_chat_users(current_user)
        
        # Annotate chat users with metadata
        chat_users = self.annotate_chat_users_compatible(potential_users, current_user)

        # --- Avatar handling ---
        def avatar_for(user, color="667eea"):
            return (
                user.profile_image.url
                if getattr(user, "profile_image", None)
                else f"https://ui-avatars.com/api/?name={user.get_full_name()}&background={color}&color=fff&size=128&bold=true"
            )

        context.update({
            "messages": chat_messages,
            "current_user": current_user,
            "other_user": other_user,
            "chat_users": chat_users,
            "default_user_avatar": avatar_for(current_user, "667eea"),
            "other_user_avatar": avatar_for(other_user, "764ba2"),
            "other_employee": Employee.objects.filter(user=other_user).first(),
            "title": f"Chat with {other_user.get_full_name()}",
            "total_messages": total_messages,
        })

        return context

    def get_potential_chat_users(self, current_user):
        """
        Get list of User IDs that current user can chat with
        Returns a queryset of User objects
        """
        if current_user.usertype == "student":
            # ✅ Students can chat with ALL mentors and teachers in their branch/course (NO HR)
            admission = Admission.objects.filter(user=current_user, is_active=True).first()
            if admission and admission.branch:
                # Get ALL mentors
                mentor_ids = Employee.objects.filter(
                    user__usertype="mentor",
                    is_active=True
                ).values_list('user_id', flat=True)
                
                # Get teachers in same branch/course
                teacher_ids = Employee.objects.filter(
                    user__usertype="teacher",
                    branch=admission.branch,
                    course=admission.course,
                    is_active=True
                ).values_list('user_id', flat=True)
                
                # ✅ NO HR - removed from here
                
                # Combine all user IDs
                all_user_ids = list(mentor_ids) + list(teacher_ids)
                
                return User.objects.filter(id__in=all_user_ids)
            else:
                return User.objects.none()

        elif current_user.usertype == "teacher":
            # Teachers can chat with students in their course/branch
            teacher_emp = Employee.objects.filter(user=current_user).first()
            if teacher_emp and teacher_emp.branch:
                student_user_ids = Admission.objects.filter(
                    branch=teacher_emp.branch,
                    course=teacher_emp.course,
                    is_active=True
                ).values_list("user_id", flat=True)
                
                return User.objects.filter(id__in=student_user_ids)
            else:
                return User.objects.none()

        elif current_user.usertype == "mentor":
            # Mentors can chat with ALL students
            student_user_ids = Admission.objects.filter(
                is_active=True
            ).values_list("user_id", flat=True)
            
            return User.objects.filter(id__in=student_user_ids)

        elif current_user.usertype in ["hr", "branch_staff"]:
            # HR/Branch staff can chat with students in their branch
            student_user_ids = Admission.objects.filter(
                branch=current_user.branch,
                is_active=True
            ).values_list("user_id", flat=True)
            
            return User.objects.filter(id__in=student_user_ids)

        else:
            # Admin/CEO/CFO/COO can see teachers and mentors (NO HR)
            employee_user_ids = Employee.objects.filter(
                user__usertype__in=["teacher", "mentor"],  # ✅ Removed "hr"
                branch=current_user.branch,
                is_active=True
            ).values_list('user_id', flat=True)
            
            return User.objects.filter(id__in=employee_user_ids)

    def annotate_chat_users_compatible(self, potential_users, current_user):
        """
        Annotate chat users with metadata - shows ALL users even without messages
        """
        annotated_users = []
        
        for user_obj in potential_users:
            # Get all messages with this user
            all_messages = ChatSession.objects.filter(
                Q(sender=user_obj, recipient=current_user) |
                Q(sender=current_user, recipient=user_obj)
            ).order_by('-created')
            
            # Find last non-deleted message
            last_msg = None
            for msg in all_messages:
                if current_user.id not in msg.deleted_by_ids:
                    last_msg = msg
                    break
            
            # Count unread non-deleted messages
            unread_count = 0
            if all_messages.exists():
                unread_msgs = ChatSession.objects.filter(
                    sender=user_obj,
                    recipient=current_user,
                    read=False
                )
                unread_count = sum(1 for msg in unread_msgs if current_user.id not in msg.deleted_by_ids)
            
            # Create user data wrapper
            class ChatUserData:
                def __init__(self, user):
                    self.user = user
                    self.last_message_time = None
                    self.last_message_text = None
                    self.last_message_sender_id = None
                    self.unread_count = 0
            
            chat_user = ChatUserData(user_obj)
            
            # ✅ Set data (works even if no messages)
            if last_msg:
                chat_user.last_message_time = last_msg.created
                chat_user.last_message_text = last_msg.message or "[Attachment]"
                chat_user.last_message_sender_id = last_msg.sender_id
            else:
                # ✅ No messages - set defaults but STILL SHOW
                chat_user.last_message_time = None
                chat_user.last_message_text = ""
                chat_user.last_message_sender_id = None
            
            chat_user.unread_count = unread_count
            
            # ✅ ALWAYS add user (no skip)
            annotated_users.append(chat_user)
        
        # Sort: Users with messages first (by time), then users without (alphabetically)
        annotated_users.sort(
            key=lambda x: (
                x.last_message_time is None,
                -x.last_message_time.timestamp() if x.last_message_time else 0,
                x.user.get_full_name()
            )
        )
        
        return annotated_users

    def post(self, request, *args, **kwargs):
        other_user = get_object_or_404(User, id=self.kwargs["user_id"])
        message_text = request.POST.get("message", "").strip()
        attachment = request.FILES.get("attachment")

        # Validate
        if attachment and attachment.size > 1024 * 1024:
            messages.error(request, "File size should not exceed 1 MB.")
            return redirect("masters:chat_view", user_id=other_user.id)

        if not message_text and not attachment:
            messages.warning(request, "Please enter a message or attach a file.")
            return redirect("masters:chat_view", user_id=other_user.id)

        # Create message
        ChatSession.objects.create(
            sender=request.user,
            recipient=other_user,
            message=message_text or "",
            attachment=attachment,
            read=False,
        )

        return redirect("masters:chat_view", user_id=other_user.id)


@login_required
@require_POST
def send_message_ajax(request):
    """Send a message via AJAX"""
    other_user_id = request.POST.get('other_user_id')
    message_text = request.POST.get('message', '').strip()
    attachment = request.FILES.get('attachment')
    
    other_user = get_object_or_404(User, id=other_user_id)
    current_user = request.user
    
    # Validate file size
    if attachment and attachment.size > 1024 * 1024:  # 1 MB
        return JsonResponse({'status': 'error', 'message': 'File size should not exceed 1 MB.'})
    
    # Validate message
    if not message_text and not attachment:
        return JsonResponse({'status': 'error', 'message': 'Please enter a message or attach a file.'})
    
    # Create message
    try:
        chat_message = ChatSession.objects.create(
            sender=current_user,
            recipient=other_user,
            message=message_text or "",
            attachment=attachment,
            read=False
        )
        
        # Return success response with message data
        return JsonResponse({
            'status': 'success',
            'message_id': chat_message.id,
            'message': chat_message.message,
            'sender_id': chat_message.sender.id,
            'sender_name': chat_message.sender.get_full_name(),
            'recipient_id': chat_message.recipient.id,
            'time': chat_message.created.strftime('%I:%M %p'),
            'timestamp': chat_message.created.isoformat(),
            'attachment_url': chat_message.attachment.url if chat_message.attachment else None,
            'attachment_name': chat_message.attachment.name if chat_message.attachment else None,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to send message: {str(e)}'})


class UpdateListView(mixins.HybridListView):
    template_name = "masters/update/list.html"
    model = Update
    table_class = tables.UpdateTable
    filterset_fields = {'created': ['exact'],}  
    permissions = ("admin_staff", "partner", "branch_staff", "teacher", "is_superuser", "student", "mentor", "tele_caller", "sales_head""ceo","cfo","coo","hr","cmo")
    branch_filter = False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Updates"
        context["is_update"] = True
        context["updates"] = context["object_list"]
        user_type = self.request.user.usertype
        context["can_add"] = user_type not in ("mentor", "student", "teacher", "tele_caller", "sales_head")
        context["new_link"] = reverse_lazy("masters:update_create")
        return context
    

class UpdateDetailView(mixins.HybridDetailView):
    template_name = "masters/update/detail.html"
    model = Update
    permissions = ("admin_staff", "partner", "branch_staff", "teacher", "student", "mentor", "tele_caller", "sales_head", "ceo","cfo","coo","hr","cmo" )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Details"
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        if request.user.is_authenticated:
            from .models import NotificationReadStatus
            NotificationReadStatus.objects.get_or_create(
                user=request.user,
                update=self.object
            )
        
        return response
    

class UpdateCreateView(mixins.HybridCreateView):
    model = Update
    permissions = ("admin_staff", "branch_staff","ceo","cfo","coo","hr","cmo", "mentor")
    exclude = ("status", "is_active", "branch")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update"
        return context

    def get_success_url(self):
        return reverse_lazy("masters:update_detail", kwargs={"pk": self.object.pk})


class UpdateUpdateView(mixins.HybridUpdateView):
    model = Update
    permissions = ("admin_staff", "branch_staff","ceo","cfo","coo","hr","cmo", "mentor")
    form_class = forms.UpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update"
        return context
    

class UpdateDeleteView(mixins.HybridDeleteView):
    model = Update
    permissions = ("admin_staff", "branch_staff","ceo","cfo","coo","hr","cmo", "mentor")


class PlacementRequestListView(mixins.HybridListView):
    model = PlacementRequest
    table_class = tables.PlacementRequestTable
    filterset_fields = {'student': ['exact'],}  
    permissions = ("admin_staff", "branch_staff", "teacher", "is_superuser", "mentor", "ceo","cfo","coo","hr","cmo")
    branch_filter = False
    template_name = "masters/placement-request/placement-request-list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Placement Request"
        context["is_placement_request"] = True
        context["can_add"] = True
        context["new_link"] = reverse_lazy("masters:placement_request_create")
        return context
    

class PlacementRequestDetailView(mixins.HybridDetailView):
    model = PlacementRequest
    permissions = ("admin_staff", "branch_staff", "teacher", "student", "mentor", "ceo","cfo","coo","hr","cmo")
    template_name = "masters/placement-request/placement-request-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Placement Request"
        return context
    

class PlacementRequestCreateView(mixins.HybridCreateView):
    model = PlacementRequest
    form_class = forms.PlacementRequestForm
    permissions = (
        "admin_staff", "branch_staff", "mentor", "student", "teacher", "ceo", "cfo", "coo", "hr", "cmo"
    )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user 
        return kwargs

    def dispatch(self, request, *args, **kwargs):

        if request.user.usertype == "student":
            try:
                admission = Admission.objects.get(user=request.user)
            except Admission.DoesNotExist:
                return self.handle_no_permission()

            if PlacementRequest.objects.filter(
                student=admission,
                status__in=["Request Send", "Under Review"]
            ).exists():
                return render(
                    request,
                    'masters/placement-request/403.html',
                    status=403
                )

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()

        if self.request.user.usertype == "student":
            try:
                admission = Admission.objects.get(user=self.request.user)
                initial["student"] = admission
            except Admission.DoesNotExist:
                pass

        return initial

    def form_valid(self, form):

        if self.request.user.usertype == "student":
            try:
                admission = Admission.objects.get(user=self.request.user)
                form.instance.student = admission
            except Admission.DoesNotExist:
                form.add_error(None, "Student record not found.")
                return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Placement Request"
        return context

    def get_success_url(self):
        return reverse_lazy("masters:placement_request_detail", kwargs={"pk": self.object.pk})


class PlacementRequestUpdateView(mixins.HybridUpdateView):
    model = PlacementRequest
    permissions = (
        "admin_staff", "branch_staff", "mentor",
        "ceo", "cfo", "coo", "hr", "cmo"
    )
    form_class = forms.PlacementRequestForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Placement Request"
        return context

    

class PlacementRequestDeleteView(mixins.HybridDeleteView):
    model = PlacementRequest
    permissions = ("admin_staff", "branch_staff", "mentor", "ceo","cfo","coo","hr","cmo")


class ActivityListView(mixins.HybridListView):
    model = Activity
    table_class = tables.ActivityTable
    filterset_fields = {'name': ['exact'], }
    permissions = ("branch_staff", "partner", "teacher", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_activity"] = True 
        context["is_master"] = True
        return context
    

class ActivityDetailView(mixins.HybridDetailView):
    model = Activity
    permissions = ("admin_staff", "partner", "branch_staff", "teacher", "student", "mentor", "tele_caller", "sales_head", "ceo","cfo","coo","hr","cmo" )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Activity Details"
        return context
    

class ActivityCreateView(mixins.HybridCreateView):
    model = Activity
    permissions = ("admin_staff", "branch_staff","ceo","cfo","coo","hr","cmo", "mentor")
    exclude = ("status", "is_active", "branch")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Activity"
        return context


class ActivityUpdateView(mixins.HybridUpdateView):
    model = Activity
    permissions = ("admin_staff", "branch_staff","ceo","cfo","coo","hr","cmo", "mentor")
    form_class = forms.ActivityForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Activity"
        return context
    

class ActivityDeleteView(mixins.HybridDeleteView):
    model = Activity
    permissions = ("admin_staff", "branch_staff","ceo","cfo","coo","hr","cmo", "mentor")


class BranchActivityListView(mixins.HybridListView):
    model = BranchActivity
    table_class = tables.BranchActivityTable
    filterset_fields = {'branch': ['exact'], 'activity': ['exact']}
    permissions = ("branch_staff", "partner", "teacher", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_branch_activity"] = True 
        context["is_master"] = True
        context['can_add'] = True
        context['new_link'] = reverse_lazy("masters:branch_activity_create")
        return context
    

class BranchActivityTableView(mixins.HybridTemplateView):
    template_name = 'masters/activity/branch_activity_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_activity_branch_table'] = True

        selected_month = self.request.GET.get('month', datetime.now().strftime('%Y-%m'))
        context['selected_month'] = selected_month

        try:
            month_date = datetime.strptime(selected_month, '%Y-%m')
            context['selected_month_name'] = month_date.strftime('%B %Y')
        except ValueError:
            context['selected_month_name'] = "Current Month"

        months = []
        current_date = datetime.now()
        for i in range(20):
            month_iter = current_date - relativedelta(months=i)
            months.append({
                'value': month_iter.strftime('%Y-%m'),
                'name': month_iter.strftime('%B %Y')
            })
        context['months'] = months

        activities = Activity.objects.filter(is_active=True).order_by('name')
        branches = Branch.objects.filter(is_active=True).order_by('name')

        activity_matrix = []
        for activity in activities:
            row = {'activity': activity, 'branches': []}
            for branch in branches:
                branch_activity = BranchActivity.objects.filter(
                    branch=branch,
                    activity=activity,
                    month=selected_month,
                    is_active=True
                ).first()

                month_points = branch_activity.point if branch_activity else 0

                total_points = BranchActivity.objects.filter(
                    branch=branch,
                    activity=activity,
                    is_active=True
                ).aggregate(total_points=Sum('point'))['total_points'] or 0

                row['branches'].append({
                    'branch': branch,
                    'points': month_points,
                    'total_points': total_points,
                    'id': branch_activity.id if branch_activity else None,
                    'is_highest': False 
                })
            activity_matrix.append(row)

        for row in activity_matrix:
            if row['branches']:
                max_points = max(b['points'] for b in row['branches'])
                for b in row['branches']:
                    b['is_highest'] = (b['points'] == max_points and max_points > 0)

        branch_totals = []
        for branch in branches:
            month_total = BranchActivity.objects.filter(
                branch=branch,
                month=selected_month,
                is_active=True
            ).aggregate(total_points=Sum('point'))['total_points'] or 0

            overall_total = BranchActivity.objects.filter(
                branch=branch,
                is_active=True
            ).aggregate(total_points=Sum('point'))['total_points'] or 0

            branch_totals.append({
                'branch': branch,
                'month_total': month_total,
                'overall_total': overall_total,
                'is_highest': False 
            })

        leading_branch = None
        if branch_totals:
            max_month_total = max(b['month_total'] for b in branch_totals)
            for b in branch_totals:
                b['is_highest'] = (b['month_total'] == max_month_total and max_month_total > 0)

            if max_month_total > 0:
                leading_branch = max(branch_totals, key=lambda x: x['month_total'])

        context.update({
            'activities': activities,
            'branches': branches,
            'activity_matrix': activity_matrix,
            'branch_totals': branch_totals,
            'leading_branch': leading_branch,
            'can_add': (
                self.request.user.is_superuser or 
                self.request.user.usertype in ["admin_staff", "ceo","cfo","coo","hr","cmo"]
            ),
            'new_link': reverse_lazy("masters:activity_create")
        })

        return context
    

class BranchActivityDetailView(mixins.HybridDetailView):
    model = BranchActivity
    permissions = ("admin_staff", "partner", "branch_staff", "teacher", "student", "mentor", "tele_caller", "sales_head", "ceo","cfo","coo","hr","cmo" )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Branch Activity Details"
        return context
    

class BranchActivityCreateView(mixins.HybridCreateView):
    model = BranchActivity
    permissions = ("is_superuser", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    form_class = forms.BranchActivityForm
    exclude = ("creator",)

    def get_initial(self):
        initial = super().get_initial()
        branch_id = self.request.GET.get("branch")
        activity_id = self.request.GET.get("activity")
        month = self.request.GET.get("month")

        if branch_id:
            initial["branch"] = branch_id
        if activity_id:
            initial["activity"] = activity_id
        if month:
            initial["month"] = month 

        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.GET.get("branch"):
            form.fields["branch"].disabled = True
        if self.request.GET.get("activity"):
            form.fields["activity"].disabled = True
        if self.request.GET.get("month"):
            form.fields["month"].disabled = True 
            form.fields["month"].initial = self.request.GET.get("month") 
        return form

    def form_valid(self, form):
        form.instance.creator = self.request.user

        branch_id = self.request.GET.get("branch")
        activity_id = self.request.GET.get("activity")
        month = self.request.GET.get("month")

        if branch_id:
            form.instance.branch_id = branch_id
        if activity_id:
            form.instance.activity_id = activity_id
        if month:
            form.instance.month = month 

        return CreateView.form_valid(self, form)
    
    def get_success_url(self):
        base_url = reverse_lazy('masters:branch_activity_table')
        month = self.request.GET.get("month") or self.object.month
        if month:
            query_string = urlencode({'month': month})
            return f"{base_url}?{query_string}"
        return base_url


class BranchActivityUpdateView(mixins.HybridUpdateView):
    model = BranchActivity
    permissions = ("admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    form_class = forms.BranchActivityForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["month"].widget.attrs["class"] = "form-select"
        return form

    def form_valid(self, form):
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Branch Activity"
        return context
    
    def get_success_url(self):
        base_url = reverse_lazy('masters:branch_activity_table')
        month = self.object.month  
        if month:
            query_string = urlencode({'month': month})
            return f"{base_url}?{query_string}"
        return base_url
    

class BranchActivityDeleteView(mixins.HybridDeleteView):
    model = BranchActivity
    permissions = ("admin_staff", "branch_staff","ceo","cfo","coo","hr","cmo", "mentor")
    

class RequestSubmissionListView(mixins.HybridListView):
    model = RequestSubmission
    table_class = tables.RequestSubmissionTable
    filterset_fields = {"title": ["exact"], "branch_staff": ["exact"], "status":['exact']}
    permissions = ()

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_superuser:
            return qs

        try:
            user_profile = Employee.objects.get(user=user)
            usertype = user_profile.user.usertype
        except Employee.DoesNotExist:  
            return qs.none()

        assigned_only = self.request.GET.get('assigned', '').lower() == 'true'

        if assigned_only:
            latest_status_subquery = RequestSubmissionStatusHistory.objects.filter(
                submission=OuterRef('pk')
            ).order_by('-date')

            qs = qs.annotate(
                latest_next_usertype=Subquery(latest_status_subquery.values('next_usertype')[:1])
            ).filter(
                latest_next_usertype=usertype,
                is_active=True
            )

            if usertype != "branch_staff":
                qs = qs.exclude(creator=user_profile.user)

            status = self.request.GET.get("status", "").lower()
            if status in ["approved", "rejected", "pending", "processing"]:
                qs = qs.filter(status=status)

            return qs.distinct()

        if usertype == "branch_staff":
            qs = qs.filter(creator=user_profile.user)

            status = self.request.GET.get("status", "").lower()
            if status in ["approved", "rejected", "pending"]:
                qs = qs.filter(status=status)
        else:
            qs = qs.filter(
                Q(status_history__next_usertype=usertype) |
                Q(status_history__submitted_users=user_profile)
            ).distinct().exclude(creator=user_profile.user)

            status = self.request.GET.get("status", "").lower()
            if status in ["approved", "rejected"]:
                hr_to_branch_staff_ids = RequestSubmissionStatusHistory.objects.filter(
                    usertype="hr",
                    next_usertype="branch_staff"
                ).values_list('submission_id', flat=True)
                qs = qs.filter(
                    id__in=hr_to_branch_staff_ids,
                    status=status
                ).distinct()
            elif status == "processing":
                qs = qs.filter(status="processing")

        return qs

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs['request'] = self.request  
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = context.get("table")
        if table:
            table._request = self.request
        context.update({
            "is_master": True,
            "is_request_submission": True,
            "can_add": False,
            "new_link": reverse_lazy("masters:request_submission_create")
        })
        return context

    
class SharedRequestsListView(mixins.HybridListView):
    model = RequestSubmission
    table_class = tables.RequestSubmissionTable
    filterset_fields = {"title": ["exact"], "branch_staff": ["exact"], "status": ['exact']}
    permissions = ()

    def get_queryset(self):
        user = self.request.user
        user_profile = Employee.objects.filter(user=user).first()
        if not user_profile:
            return RequestSubmission.objects.none()

        return RequestSubmission.objects.filter(
            request_shared_usertype__user=user,
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "is_master": True,
            "is_shared_requests": True,
            "can_add": False,
            "new_link": reverse_lazy("masters:request_submission_create")
        })
        return context


class MyRequestSubmissionListView(mixins.HybridListView):
    model = RequestSubmission
    table_class = tables.MyRequestSubmissionTable
    filterset_fields = {"title": ["exact"], "branch_staff": ["exact"], "status": ["exact"]}
    permissions = ()

    def get_queryset(self):
        user = self.request.user
        usertype = user.usertype

        try:
            user_profile = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return RequestSubmission.objects.none()

        qs = RequestSubmission.objects.filter(created_by=user_profile)

        latest_next_usertype = RequestSubmissionStatusHistory.objects.filter(
            submission=OuterRef('pk')
        ).order_by('-date').values('next_usertype')[:1]

        qs = qs.annotate(latest_status=Subquery(latest_next_usertype))

        if usertype == "coo":
            assigned_back_filter = Q(latest_status="coo")
        else:
            latest_usertype_from_hr = RequestSubmissionStatusHistory.objects.filter(
                submission=OuterRef('pk'),
                usertype="hr"
            ).order_by('-date').values('next_usertype')[:1]

            assigned_back_filter = Q(
                latest_status=Subquery(latest_usertype_from_hr)
            ) & Q(latest_status=usertype)

        qs = qs.filter(
            Q(created_by=user_profile) | assigned_back_filter
        )

        return qs.annotate(
            hr_assigned_to_creator=Exists(
                RequestSubmissionStatusHistory.objects.filter(
                    submission=OuterRef("pk"),
                    usertype="hr",
                    next_usertype=OuterRef("creator__usertype")
                )
            ),
            hr_assigned_to_me=Exists(
                RequestSubmissionStatusHistory.objects.filter(
                    submission=OuterRef("pk"),
                    usertype="hr",
                    next_usertype=usertype
                )
            ),
            submitted_by_me=Exists(
                RequestSubmissionStatusHistory.objects.filter(
                    submission=OuterRef("pk"),
                    submitted_users=user_profile
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "is_master": True,
            "is_my_request_submission": True,
            "can_add": False,
            "new_link": reverse_lazy("masters:request_submission_create"),
        })
        return context


class RequestSubmissionDetailView(mixins.HybridDetailView):
    template_name = "masters/request_submission/request_submission_detail.html"
    model = RequestSubmission
    permissions = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        context["can_delete"] = mixins.check_access(self.request, ("is_superuser", "coo"))

        latest_status = self.object.status_history.first()
        context["latest_next_usertype"] = latest_status.next_usertype if latest_status else None
        context["latest_status"] = latest_status

        try:
            user_profile = Employee.objects.get(user=self.request.user)
        except Employee.DoesNotExist:
            user_profile = None

        is_branch_staff_user_of_creator = (
            self.request.user.usertype == "branch_staff"
            and self.object.branch == user_profile.branch
        )

        context["is_branch_staff_user_of_creator"] = is_branch_staff_user_of_creator

        if user_profile or self.request.user.is_superuser:
            context["status_history"] = self.object.status_history.all()
        
        else:
            context["status_history"] = []

        context["latest_submitted_user_ids"] = (
            list(latest_status.submitted_users.values_list('user__id', flat=True))
            if latest_status else []
        )

        shared_usertypes = obj.request_shared_usertype.values_list('user__usertype', flat=True)
        context["is_usertype_shared"] = self.request.user.usertype in shared_usertypes

        return context

class RequestSubmissionCreateView(mixins.HybridCreateView):
    model = RequestSubmission
    template_name = "masters/request_submission/request_submission_create_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Request Submission"
        context["is_request_submission_form"] = True
        context['current_usertype'] = self.request.user.usertype

        if self.request.user.usertype == "hr":
            usertype_choices = list(USERTYPE_CHOICES)
            excluded_usertypes = ['branch_staff', 'hr', 'coo']
            context['available_flow_usertypes'] = [
                (value, label) for value, label in usertype_choices
                if value not in excluded_usertypes
            ]
            if 'form' not in context or context['form'] is None:
                context['form'] = self.get_form()
            context['form'].fields['usertype_flow'].initial = []

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_usertype = self.request.user.usertype
        allowed_fields = ['title', 'description', 'attachment']

        if user_usertype == "hr":
            form.fields['usertype_flow'] = MultipleChoiceField(
                choices=[(v, l) for v, l in USERTYPE_CHOICES if v not in ['branch_staff', 'hr', 'coo']],
                required=False,
                widget=MultipleHiddenInput()  
            )
            form.fields['user_flow'] = form.fields['usertype_flow']
            allowed_fields.append('usertype_flow')

        for field_name in list(form.fields):
            if field_name not in allowed_fields:
                del form.fields[field_name]

        return form

    def form_invalid(self, form):
        print("FORM ERRORS:", form.errors) 
        return super().form_invalid(form)

    @transaction.atomic
    def form_valid(self, form):
        user_profile = Employee.objects.get(user=self.request.user)
        form.instance.branch_staff = user_profile
        form.instance.created_by = user_profile

        try:
            if user_profile.user.usertype == "hr":
                selected_usertypes = [
                    ut for ut in self.request.POST.getlist('usertype_flow') if ut.strip()
                ]

                full_flow = ["hr"] + selected_usertypes + ["coo"]

                form.instance.usertype_flow = full_flow  

                form.instance.status = "pending"
                form.instance.current_usertype = selected_usertypes[0] if selected_usertypes else "coo"

            else:
                form.instance.usertype_flow = [user_profile.user.usertype, "hr"]
                form.instance.status = "pending"
                form.instance.current_usertype = "hr"

            response = super().form_valid(form)

            RequestSubmissionStatusHistory.objects.create(
                submission=form.instance,
                user=user_profile,
                usertype=user_profile.user.usertype,
                next_usertype=form.instance.current_usertype,
                status='pending',
                remark=f"{user_profile.user.usertype} created the request."
            )

            next_profiles = Employee.objects.filter(user__usertype=form.instance.current_usertype)
            # for profile in next_profiles:
            #     Notification.objects.create(
            #         user=profile.user,
            #         message=f"New request assigned: {form.instance.title}",
            #         url=form.instance.get_absolute_url(),
            #     )

            return response

        except Exception as e:
            print("ERROR SAVING REQUEST:", e)
            return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('masters:request_submission_detail', kwargs={'pk': self.object.pk})
    
    
class RequestStatusUpdateView(mixins.HybridUpdateView):
    model = RequestSubmission
    form_class = forms.RequestStatusUpdateForm
    template_name = "masters/request_submission/request_submission_form.html"

    def get_next_usertype(self, submission, current_usertype):
        """Get the next usertype in the flow"""
        flow = submission.usertype_flow or []
        try:
            current_index = flow.index(current_usertype)
            if current_index > 0 and flow[current_index - 1] == "coo":
                return "coo"
            elif current_index + 1 < len(flow):
                return flow[current_index + 1]
            else:
                return None
        except ValueError:
            return None
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['usertype'] = self.request.user.usertype.lower()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usertype_choices'] = USERTYPE_FLOW_CHOICES
        
        # COO specific context for reassignment
        if self.request.user.usertype == 'coo' and hasattr(self.object, 'usertype_flow'):
            usertype_labels = dict(USERTYPE_FLOW_CHOICES)
            flow = self.object.usertype_flow or []
            reassign_choices = [
                (key, usertype_labels.get(key, key))
                for key in flow
                if key != 'coo'
            ]
            context['reassign_usertype_choices'] = reassign_choices
        
        context['next_usertype'] = self.get_next_usertype(self.object, self.request.user.usertype)
        return context

    def get_next_in_flow(self, flow_list, current_usertype, submission=None):
        """Return the next usertype in flow or fallback to creator's usertype."""
        try:
            # If HR reviewing a user-closed request — send back to creator
            if current_usertype == "hr" and submission and submission.is_request_closed_by_users == "true":
                creator_usertype = submission.created_by.user.usertype if submission.created_by else None
                if creator_usertype:
                    return creator_usertype

            idx = flow_list.index(current_usertype)
            # If not last in flow, return the next one
            if idx + 1 < len(flow_list):
                return flow_list[idx + 1]

            # If HR is the last in flow, send back to creator
            if current_usertype == "hr" and submission and submission.created_by:
                return submission.created_by.user.usertype
        except ValueError:
            pass

        # Fallback to creator if nothing else found
        if submission and submission.created_by:
            return submission.created_by.user.usertype
        return None

    @transaction.atomic
    def form_valid(self, form):
        user_profile = Employee.objects.get(user=self.request.user)
        submission = form.instance
        current_usertype = user_profile.user.usertype
        flow_list = submission.usertype_flow or []

        # 1. FLOW CREATION / UPDATE (for HR)
        if not submission.pk or current_usertype == "hr":
            creator_usertype = (
                submission.created_by.user.usertype if submission.created_by else
                (flow_list[0] if flow_list else current_usertype)
            )
            new_flow = [creator_usertype]
            if "hr" not in new_flow: new_flow.append("hr")
            
            middle_usertypes = self.request.POST.getlist("user_flow") or []
            middle_usertypes = [ut.strip() for ut in middle_usertypes if ut.strip() not in ["hr", "coo", creator_usertype]]
            
            for ut in middle_usertypes:
                if ut not in new_flow: new_flow.append(ut)
            if "coo" not in new_flow: new_flow.append("coo")
            
            submission.usertype_flow = new_flow
            flow_list = new_flow

        # 2. EXTRACT FORM DATA
        # Use users_status if provided (usually by intermediate users), otherwise use status field
        form_status = form.cleaned_data.get("status")
        users_status = form.cleaned_data.get("users_status")
        
        # Logic to determine the active decision status from the current form
        if current_usertype not in ["hr", "coo"] and users_status:
            current_decision_status = users_status
        else:
            current_decision_status = form_status or "forwarded"

        reassign_to = form.cleaned_data.get("reassign_usertype")
        end_request_flow = form.cleaned_data.get("end_request_flow")
        remark = form.cleaned_data.get("remark", "")
        next_usertype = None
        
        creator_usertype = submission.created_by.user.usertype if submission.created_by else None

        # 3. DETERMINE NEXT USERTYPE
        if current_usertype not in ["hr", "coo", "branch_staff"]:
            # Regular users (CMO, etc.)
            if form.cleaned_data.get("is_request_closed_by_users") == "true":
                submission.is_request_closed_by_users = "true"
                next_usertype = "hr"  # Send back to HR for final sign-off
            else:
                submission.is_request_closed_by_users = "false"
                next_usertype = self.get_next_in_flow(flow_list, current_usertype, submission)

        elif current_usertype == "coo":
            if current_decision_status == "re_assign":
                next_usertype = "coo"
                current_decision_status = "forwarded"
            elif current_decision_status in ["approved", "rejected"]:
                next_usertype = "hr"  # COO decisions go to HR
            else:
                next_usertype = self.get_next_in_flow(flow_list, current_usertype, submission)

        elif current_usertype == "hr":
            if end_request_flow == "true" or reassign_to == creator_usertype:
                next_usertype = creator_usertype
            else:
                next_usertype = self.get_next_in_flow(flow_list, current_usertype, submission)

        # ---------------------------------------------------------
        # 4. FIX: STATUS RESOLUTION & COMPLETION LOGIC
        # ---------------------------------------------------------
        
        # If the request is going to the creator, we need to find the FINAL status
        if next_usertype == creator_usertype:
            # 1. Check if the current user (HR) provided a decision status
            if current_decision_status in ["approved", "rejected"]:
                final_status = current_decision_status
            else:
                # 2. Look back in history for the last person who Approved or Rejected
                last_decision = submission.status_history.filter(
                    status__in=["approved", "rejected"]
                ).order_by("-created").first()
                
                if last_decision:
                    final_status = last_decision.status
                else:
                    # Fallback if somehow no decision was recorded
                    final_status = "approved" 

            submission.status = final_status
            submission.is_request_completed = "true"
        else:
            # Request is still in progress (Forwarding)
            submission.status = current_decision_status
            submission.is_request_completed = "false"

        # ---------------------------------------------------------
        
        # 5. SAVE SUBMISSION
        submission.current_usertype = next_usertype
        submission.updated_by = user_profile
        submission.save()

        # 6. SHARED USERTYPES
        shared_usertype = form.cleaned_data.get("request_shared_usertype")
        if shared_usertype:
            submission.request_shared_usertype.set(shared_usertype)
        else:
            submission.request_shared_usertype.clear()

        # 7. HISTORY RECORD
        history_record = RequestSubmissionStatusHistory.objects.create(
            submission=submission,
            user=user_profile,
            usertype=current_usertype,
            status=submission.status, # Save the resolved status
            remark=remark,
            next_usertype=next_usertype or "",
        )
        history_record.submitted_users.add(user_profile)

        return redirect("masters:request_submission_detail", pk=submission.pk)

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)
    

class RequestSubmissionDeleteView(mixins.HybridDeleteView):
    model = RequestSubmission
    permissions = ("coo", "is_superuser")


def download_request_submission_pdf(request, pk):
    instance = get_object_or_404(RequestSubmission, pk=pk)

    # Determine which remark to show based on current usertype
    if request.user.usertype == "hr":
        # Get latest coo remark
        last_remark = (
            instance.status_history
            .filter(usertype="coo", remark__isnull=False)
            .order_by("-date")
            .first()
        )
    else:
        # Get latest hr remark (or fallback as needed)
        last_remark = (
            instance.status_history
            .filter(usertype="hr", remark__isnull=False)
            .order_by("-date")
            .first()
        )

    full_text = last_remark.remark if last_remark else ""

    # Word splitting for pages
    first_page_length = 370
    other_page_length = 423

    words = full_text.split()
    chunks = []
    if len(words) > first_page_length:
        chunks.append(' '.join(words[:first_page_length]))
        for i in range(first_page_length, len(words), other_page_length):
            chunks.append(' '.join(words[i:i + other_page_length]))
    else:
        chunks.append(' '.join(words))

    context = {
        "instance": instance,
        "chunks": chunks,
        "request": request,
    }

    html_string = render_to_string(
        'masters/request_submission/pdf/request_submission_pdf.html',
        context
    )
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))

    pdf_file = html.write_pdf(stylesheets=[
        CSS(string='''
            @page {
                size: A4;
                margin: 0mm;
            }
        ''')
    ])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="request_submission.pdf"'
    return response


class RequestSubmissionPDFDownloadView(PDFView):
    template_name = 'masters/request_submission/pdf/request_submission_download_pdf.html'
    pdfkit_options = {
        "page-width": 210,
        "page-height": 297,
        "encoding": "UTF-8",
        "margin-top": "0",
        "margin-bottom": "0",
        "margin-left": "0",
        "margin-right": "0",
        "enable-smart-shrinking": "",
        "zoom": 0.8,
        "minimum-font-size": 8,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = get_object_or_404(RequestSubmission, pk=self.kwargs["pk"])
        context["title"] = "Request Submission"
        context["instance"] = instance

        coo_remark = (
            instance.status_history
            .filter(usertype="coo", remark__isnull=False)
            .order_by("-date")
            .first()
        )

        context["coo_remark"] = coo_remark.remark if coo_remark else ""
        return context
    
    def get_filename(self):
        return "request_submissions.pdf"


class LeaveRequestListView(mixins.HybridListView):
    model = LeaveRequest
    table_class = tables.LeaveRequestTable
    template_name = "masters/leave_request/leave_request_list.html"
    filterset_fields = {'student': ['exact'], 'status': ['exact'], 'student__branch': ['exact'], 'student__course': ['exact'], 'start_date': ['exact'], 'end_date': ['exact']}
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)

        if self.request.user.usertype == "student":
            qs = qs.filter(creator=self.request.user)
        elif self.request.user.usertype == "teacher":
            qs = qs.filter(student__course=self.request.user.employee.course, student__branch=self.request.user.employee.branch)
        elif self.request.user.usertype == "mentor":
            qs = qs.filter(is_active=True)
        else:
            qs = qs.none()

        status = self.request.GET.get("status")
        if status in ["approved", "rejected", "pending"]:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.usertype == "student":
            qs = self.get_queryset().model.objects.filter(creator=self.request.user, is_active=True)
        elif self.request.user.usertype == "teacher":
            qs = self.get_queryset().model.objects.filter(is_active=True, student__course=self.request.user.employee.course, student__branch=self.request.user.employee.branch)
        elif self.request.user.usertype == "mentor":
            qs = self.get_queryset().model.objects.filter(is_active=True)
        else:
            qs = self.get_queryset().model.objects.filter(is_active=True)


        context["can_add"] = False
        context["permission_users"] = ["admin_staff", "mentor", "ceo","cfo","coo", "teacher",]

        context["status_counts"] = {
            "approved": qs.filter(status="approved").count(),
            "rejected": qs.filter(status="rejected").count(),
            "pending": qs.filter(status="pending").count(),
            "all": qs.filter(is_active=True).count(),
        }
        return context
    

class LeaveRequestDetailView(mixins.HybridDetailView):
    model = LeaveRequest
    permissions = ("admin_staff", "hr", "student", "mentor", "ceo","cfo","coo", "teacher",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Leave Request Details"
        return context
    

class LeaveRequestCreateView(mixins.HybridCreateView):
    model = LeaveRequest
    permissions = ("student",)
    form_class = forms.LeaveRequestForm
    exclude = ("creator", "branch")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_leave_request_form'] = True
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        usertype = user.usertype

        is_create = not form.instance.pk

        if usertype == "student":
            student_profile = Admission.objects.filter(user=user).first()
            if student_profile:
                form.instance.student = student_profile

        elif usertype == "mentor":
            mentor_profile = Employee.objects.filter(user=user).first()
            if mentor_profile:
                form.instance.mentor = mentor_profile
                form.instance.branch = mentor_profile.branch

        form.instance.creator = user
        if is_create:
            form.instance.status = "pending"

        response = super().form_valid(form)
        
        if is_create:
            self.send_leave_notification()
            
        return response

    def send_leave_notification(self):
        try:
            if not self.initialize_firebase():
                messages.warning(self.request, "Leave created but notification service unavailable")
                return

            leave_request = self.object
            student = leave_request.student
            if not student or not student.branch:
                return

            base_qs = (FCMDevice.objects
                    .filter(
                        user__employee__user__usertype="teacher",
                        user__employee__branch=student.branch,
                        user__employee__course=student.course,
                        user__employee__is_active=True,
                        active=True
                    ))

            latest_ids = (base_qs.values('registration_id')
                                .annotate(latest_id=Max('id'))
                                .values_list('latest_id', flat=True))
            devices = FCMDevice.objects.filter(id__in=list(latest_ids))
            if not devices.exists():
                return

            tokens = [d.registration_id for d in devices if d.registration_id]

            student_name = getattr(student, 'fullname', 'Student')
            if callable(student_name):
                student_name = student_name()

            payload_data = {
                "type": "leave_request",
                "leave_id": str(leave_request.pk),
                "student_name": student_name,
                "title": "New Leave Request",
                "body": f"{student_name} requested leave",
                "tag": f"leave-{leave_request.pk}" 
            }

            multicast = messaging.MulticastMessage(
                tokens=tokens,
                data=payload_data,
                android=messaging.AndroidConfig(
                    collapse_key=f"leave-{leave_request.pk}",
                    priority="high"
                ),
                webpush=messaging.WebpushConfig(
                    headers={
                        "Topic": f"leave-{leave_request.pk}"
                    }
                ),
            )

            resp = messaging.send_each_for_multicast(multicast)

            bad = []
            for idx, r in enumerate(resp.responses):
                if not r.success:
                    code = getattr(r.exception, 'code', '') or ''
                    if code in ('registration-token-not-registered',
                                'invalid-argument', 'invalid-registration-token'):
                        bad.append(tokens[idx])
            if bad:
                FCMDevice.objects.filter(registration_id__in=bad).update(active=False)

            if resp.success_count:
                messages.success(self.request, f"Leave created and notification sent to {resp.success_count} device(s)!")
            else:
                messages.warning(self.request, "Leave created but couldn't send notifications")

        except Exception as e:
            print(f"Notification error: {e}")
    
    def initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            import firebase_admin
            from firebase_admin import credentials
            from django.conf import settings
            
            # Check if already initialized
            if firebase_admin._apps:
                print("✅ Firebase already initialized")
                return True
            
            # Get credential path
            cred_path = getattr(settings, 'FIREBASE_CREDENTIAL_PATH', None)
            if not cred_path:
                print("❌ FIREBASE_CREDENTIAL_PATH not set in settings")
                return False
            
            import os
            if not os.path.exists(cred_path):
                print(f"❌ Firebase credential file not found: {cred_path}")
                return False
            
            # Initialize Firebase
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            return False

    def send_fcm_notification(self, registration_token, student_name, leave_request):
        """Send FCM notification"""
        try:
            from firebase_admin import messaging
            
            message = messaging.Message(
                token=registration_token,
                notification=messaging.Notification(
                    title="New Leave Request",
                    body=f"{student_name} requested leave",
                ),
                data={
                    "type": "leave_request",
                    "leave_id": str(leave_request.pk),
                    "student_name": student_name
                }
            )
            
            response = messaging.send(message)
            print(f"📨 FCM response: {response}")
            return True
            
        except Exception as e:
            print(f"❌ FCM error: {e}")
            return False

    def get_success_url(self):
        return reverse_lazy('masters:leave_request_list')
    

class LeaveRequestUpdateView(mixins.HybridUpdateView):
    model = LeaveRequest
    permissions = ("mentor", "teacher",)
    form_class = forms.LeaveRequestForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["start_date"].widget.attrs["class"] = "form-control"
        form.fields["end_date"].widget.attrs["class"] = "form-control"
        form.fields["reason"].widget.attrs["class"] = "form-control"
        form.fields["status"].widget.attrs["class"] = "form-select"
        return form
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        if form.instance.status.lower() == "approved":
            student = form.instance.student
            start_date = form.instance.start_date
            end_date = form.instance.end_date

            print(f"Approving leave for student: {student.fullname()}, from {start_date} to {end_date}")

            current_date = start_date
            while current_date <= end_date:
                try:
                    # Create or get AttendanceRegister
                    register, created = AttendanceRegister.objects.get_or_create(
                        branch=student.branch,
                        batch=student.batch,
                        date=current_date,
                        course=student.course,
                    )
                    register.save() 
                    print(f"AttendanceRegister for {current_date}: {'Created' if created else 'Exists'} | ID: {register.id}")

                    # Create or update Attendance
                    attendance, att_created = Attendance.objects.update_or_create(
                        student=student,
                        register=register,
                        defaults={"status": "Absent"}
                    )
                    attendance.save() 
                    print(f"Attendance for {student.fullname()} on {current_date}: {'Created' if att_created else 'Updated'} | ID: {attendance.id} | Status: {attendance.status}")

                except Exception as e:
                    print(f"Error marking attendance for {student.fullname()} on {current_date}: {e}")

                current_date += timedelta(days=1)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Leave Request"
        return context
    
    def get_success_url(self):
        return reverse_lazy('masters:leave_request_list')

    
class LeaveRequestDeleteView(mixins.HybridDeleteView):
    model = LeaveRequest
    permissions = ("mentor", "teacher",)


class FeedbackQuestionList(mixins.HybridListView):
    model = FeedbackQuestion
    table_class = tables.FeedbackQuestionTable
    filterset_fields = {'feedback_type': ['exact'],}
    permissions = ("branch_staff", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "tele_caller", "sales_head", "mentor")
    branch_filter = False
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_feedback_question"] = True 
        context["can_add"] = True
        context["new_link"] = reverse_lazy('masters:feedback_question_create')
        return context
    

class FeedbackQuestionDetailView(mixins.HybridDetailView):
    model = FeedbackQuestion
    permissions = ("branch_staff","admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "masters/feedback/feedback_question/feedback_question_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_feedback_question"] = True
        context["title"] = "Feedback Question"
        return context
    

class FeedbackQuestionCreateView(mixins.HybridCreateView):
    model = FeedbackQuestion
    permissions = ("is_superuser", "branch_staff", )
    exclude = ('is_active',)
    template_name = "masters/feedback/feedback_question/feedback_question_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["feedback_answer_formset"] = FeedbackAnswerFormSet(
                self.request.POST, self.request.FILES
            )
        else:
            context["feedback_answer_formset"] = FeedbackAnswerFormSet()
        context['title'] = "New Feedback Question"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        feedback_answer_formset = context["feedback_answer_formset"]

        try:
            with transaction.atomic():
                self.object = form.save()
                feedback_answer_formset.instance = self.object

                if feedback_answer_formset.is_valid():
                    feedback_answer_formset.save()
                else:
                    # Show formset errors in the form
                    for subform in feedback_answer_formset.forms:
                        for field, errors in subform.errors.items():
                            for error in errors:
                                subform.add_error(field, error)
                    # Non-field errors
                    for error in feedback_answer_formset.non_form_errors():
                        form.add_error(None, error)
                    return self.form_invalid(form)

        except IntegrityError as e:
            # Catch database-level unique constraint errors
            form.add_error(None, "Duplicate answer value or question order is not allowed.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        # Optionally, print errors to console for debugging
        print(form.errors)
        return super().form_invalid(form)
    

class FeedbackQuestionUpdateView(mixins.HybridUpdateView):
    model = FeedbackQuestion
    permissions = ("is_superuser", "admin_staff", "branch_staff", "ceo", "cfo", "coo", "hr", "cmo", "mentor")
    template_name = "masters/feedback/feedback_question/feedback_question_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback_question = self.get_object()

        active_answers = FeedbackAnswer.objects.filter(
            question=feedback_question,
            is_active=True
        )

        if self.request.POST:
            context['feedback_answer_formset'] = FeedbackAnswerFormSet(
                self.request.POST,
                self.request.FILES,
                instance=feedback_question,
                queryset=active_answers
            )
        else:
            context['feedback_answer_formset'] = FeedbackAnswerFormSet(
                instance=feedback_question,
                queryset=active_answers
            )

        context["title"] = "Update Feedback Question"
        context["is_feedback_question"] = True
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        feedback_answer_formset = context["feedback_answer_formset"]

        try:
            with transaction.atomic():
                self.object = form.save()

                feedback_answer_formset.instance = self.object
                if feedback_answer_formset.is_valid():
                    feedback_answer_formset.save()
                else:
                    # Formset validation errors
                    return self.form_invalid(form)

        except IntegrityError as e:
            # Catch database-level unique constraint errors
            form.add_error(None, "Duplicate answer value for this question is not allowed.")
            return self.form_invalid(form)

        return super().form_valid(form)


class FeedbackQuestionDeleteView(mixins.HybridDeleteView):
    model = FeedbackQuestion
    permissions = ("is_superuser","admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class FeedbackListView(mixins.HybridListView):
    model = Feedback
    table_class = tables.FeedbackTable
    filterset_fields = {'name': ['exact'], }
    permissions = ("branch_staff", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "tele_caller", "sales_head", "mentor")
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_feedback"] = True 
        context["is_master"] = True
        return context
    

class FeedbackDetailView(mixins.HybridDetailView):
    model = Feedback
    permissions = ("branch_staff","admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_feedback_detail"] = True
        context["is_master"] = True
        context["title"] = "Feedback"
        return context
    

class FeedbackCreateView(mixins.HybridCreateView):
    model = Feedback
    permissions = ("is_superuser", "student", "branch_staff", )
    template_name = "masters/feedback/feedback_form.html"
    
    def get_form_class(self):
        from django import forms
        from admission.models import Admission
        
        # Create a dynamic form class
        if hasattr(self.request.user, 'usertype') and self.request.user.usertype == 'student':
            # For students - no student field
            class FeedbackForm(forms.Form):
                comment = forms.CharField(
                    widget=forms.Textarea(attrs={'rows': 4}),
                    required=False,
                    label="Additional Comments"
                )
        else:
            # For admin/staff - include student field
            class FeedbackForm(forms.Form):
                student = forms.ModelChoiceField(
                    queryset=Admission.objects.filter(is_active=True),
                    required=True,
                    label="Student"
                )
                comment = forms.CharField(
                    widget=forms.Textarea(attrs={'rows': 4}),
                    required=False,
                    label="Additional Comments"
                )
        
        return FeedbackForm

    def get_form(self, form_class=None):
        # Don't call parent's get_form as it passes instance which we don't need
        form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Remove 'instance' since we're using a regular Form, not ModelForm
        if 'instance' in kwargs:
            del kwargs['instance']
        return kwargs

    def form_valid(self, form):
        try:
            print("Form is valid, starting feedback processing...")
            
            # Get student
            if hasattr(self.request.user, 'usertype') and self.request.user.usertype == 'student':
                student = self.get_student_from_user()
                if not student:
                    form.add_error(None, "Unable to find student information.")
                    return self.form_invalid(form)
            else:
                # For admin/staff, get student from form
                student = form.cleaned_data.get('student')
                if not student:
                    form.add_error(None, "Please select a student.")
                    return self.form_invalid(form)

            print(f"Student: {student}")
            comment = form.cleaned_data.get('comment', '')
            print(f"Comment: {comment}")

            # Process feedback questions and answers - create individual Feedback objects
            success = self.process_feedback_data(student, comment)
            if not success:
                form.add_error(None, "Failed to save feedback responses. Please try again.")
                return self.form_invalid(form)

            print("Feedback processing completed successfully!")
            return HttpResponseRedirect(self.get_success_url())

        except Exception as e:
            print(f"Error in form_valid: {e}")
            import traceback
            traceback.print_exc()
            form.add_error(None, f"An error occurred while saving feedback: {str(e)}")
            return self.form_invalid(form)

    def process_feedback_data(self, student, comment):
        """Process the custom feedback questions and answers from the form"""
        try:
            print("Processing feedback data...")
            print("POST data:", dict(self.request.POST))
            
            saved_count = 0
            # Find all question IDs in the POST data
            for key, value in self.request.POST.items():
                if key.startswith('question_'):
                    question_id = value
                    answer_key = key.replace('question_', 'answer_')
                    answer_id = self.request.POST.get(answer_key)
                    
                    print(f"Processing - Question ID: {question_id}, Answer ID: {answer_id}")
                    
                    if question_id and answer_id:
                        try:
                            # Validate that question and answer exist
                            question = FeedbackQuestion.objects.get(id=question_id, is_active=True)
                            answer = FeedbackAnswer.objects.get(id=answer_id, is_active=True)
                            
                            # Create individual Feedback object for each question-answer pair
                            feedback = Feedback(
                                student=student,
                                question=question,
                                answer=answer,
                                comment=comment,
                                is_active=True
                            )
                            feedback.save()
                            saved_count += 1
                            print(f"✓ Saved feedback #{saved_count}: Q{question_id} → A{answer_id}")
                            
                        except FeedbackQuestion.DoesNotExist:
                            print(f"✗ Error: Question {question_id} not found or inactive")
                            continue
                        except FeedbackAnswer.DoesNotExist:
                            print(f"✗ Error: Answer {answer_id} not found or inactive")
                            continue
                        except Exception as e:
                            print(f"✗ Error saving feedback for Q{question_id}: {e}")
                            continue
            
            print(f"Successfully saved {saved_count} feedback responses")
            return saved_count > 0  # Return True if at least one feedback was saved
            
        except Exception as e:
            print(f"Error in process_feedback_data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_student_from_user(self):
        """
        Get the student instance associated with the logged-in user.
        """
        try:
            from admission.models import Admission
            # Try to get the Admission record for the current user
            admission = Admission.objects.get(user=self.request.user, is_active=True)
            print(f"Found student: {admission}")
            return admission
        except Admission.DoesNotExist:
            print(f"Error: No active Admission found for user {self.request.user}")
            return None
        except Exception as e:
            print(f"Error getting student: {e}")
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "New Feedback"
        context["is_feedback"] = True
        
        # Check if user has already submitted feedback
        if hasattr(self.request.user, 'usertype') and self.request.user.usertype == 'student':
            student = self.get_student_from_user()
            if student:
                context['current_student'] = student
                # Check if student has already submitted any feedback
                has_submitted = Feedback.objects.filter(
                    student=student, 
                    is_active=True
                ).exists()
                context['user_has_submitted_feedback'] = has_submitted
        
        # Get active questions grouped by feedback type
        questions = FeedbackQuestion.get_active_questions()
        questions_by_type = {}
        
        for question in questions:
            if question.feedback_type not in questions_by_type:
                questions_by_type[question.feedback_type] = []
            questions_by_type[question.feedback_type].append(question)
        
        context['questions_by_type'] = questions_by_type
        context['feedback_types'] = FEEDBACK_TYPE_CHOICES
        
        return context

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        print("POST data:", dict(self.request.POST))
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("core:home")


class FeedbackUpdateView(mixins.HybridUpdateView):
    model = Feedback
    permissions = ("is_superuser", "admin_staff", "branch_staff", "ceo", "cfo", "coo", "hr", "cmo", "mentor")
    template_name = "masters/feedback/feedback_form.html"
    
    def get_form_class(self):
        from django import forms
        from admission.models import Admission
        
        # Create a dynamic form class
        class FeedbackForm(forms.Form):
            student = forms.ModelChoiceField(
                queryset=Admission.objects.filter(is_active=True),
                required=True,
                label="Student",
                disabled=True  # Student shouldn't be changed in update
            )
            comment = forms.CharField(
                widget=forms.Textarea(attrs={'rows': 4}),
                required=False,
                label="Additional Comments"
            )
        
        return FeedbackForm

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        kwargs = self.get_form_kwargs()
        
        # Remove 'instance' since we're using a regular Form, not ModelForm
        if 'instance' in kwargs:
            del kwargs['instance']
            
        # Set initial values
        kwargs['initial'] = {
            'student': self.object.student,
            'comment': self.object.comment,
        }
        
        return form_class(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Remove 'instance' since we're using a regular Form, not ModelForm
        if 'instance' in kwargs:
            del kwargs['instance']
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Update Feedback"
        context["is_feedback"] = True
        context['object'] = self.object  # Ensure object is available in template
        
        # Get all feedback entries for this student and comment (grouped by session)
        # We need to find all Feedback objects with the same student and comment
        # to represent one feedback session
        feedback_entries = Feedback.objects.filter(
            student=self.object.student,
            comment=self.object.comment,
            is_active=True
        ).select_related('question', 'answer')
        
        # Group questions by feedback type
        questions_by_type = {}
        # Store current answers for pre-selection
        current_answers = {}
        
        for feedback in feedback_entries:
            question = feedback.question
            if question.feedback_type not in questions_by_type:
                questions_by_type[question.feedback_type] = []
            
            # Add question to the appropriate type list if not already there
            if question not in questions_by_type[question.feedback_type]:
                questions_by_type[question.feedback_type].append(question)
            
            # Store the current answer for this question
            current_answers[str(question.id)] = str(feedback.answer.id)
        
        context['questions_by_type'] = questions_by_type
        context['feedback_types'] = FEEDBACK_TYPE_CHOICES
        context['current_answers'] = current_answers
        context['current_student'] = self.object.student
        
        return context

    def form_valid(self, form):
        try:
            print("Form is valid, starting feedback update processing...")
            
            # Get the existing student (shouldn't change in update)
            student = self.object.student
            comment = form.cleaned_data.get('comment', '')
            
            print(f"Updating feedback for Student: {student}")
            print(f"New Comment: {comment}")

            # Process feedback questions and answers - update existing Feedback objects
            success = self.process_feedback_data(student, comment)
            if not success:
                form.add_error(None, "Failed to update feedback responses. Please try again.")
                return self.form_invalid(form)

            print("Feedback update completed successfully!")
            return HttpResponseRedirect(self.get_success_url())

        except Exception as e:
            print(f"Error in form_valid: {e}")
            import traceback
            traceback.print_exc()
            form.add_error(None, f"An error occurred while updating feedback: {str(e)}")
            return self.form_invalid(form)

    def process_feedback_data(self, student, comment):
        """Process the custom feedback questions and answers from the form for update"""
        try:
            print("Processing feedback update data...")
            print("POST data:", dict(self.request.POST))
            
            # First, deactivate all existing feedback entries for this student with the same comment
            # This effectively "deletes" the old feedback session
            old_feedback_count = Feedback.objects.filter(
                student=student,
                comment=self.object.comment,  # Use the original comment to find old entries
                is_active=True
            ).update(is_active=False)
            
            print(f"Deactivated {old_feedback_count} old feedback entries")
            
            saved_count = 0
            # Find all question IDs in the POST data and create new entries
            for key, value in self.request.POST.items():
                if key.startswith('question_'):
                    question_id = value
                    answer_key = key.replace('question_', 'answer_')
                    answer_id = self.request.POST.get(answer_key)
                    
                    print(f"Processing - Question ID: {question_id}, Answer ID: {answer_id}")
                    
                    if question_id and answer_id:
                        try:
                            # Validate that question and answer exist
                            question = FeedbackQuestion.objects.get(id=question_id, is_active=True)
                            answer = FeedbackAnswer.objects.get(id=answer_id, is_active=True)
                            
                            # Create new Feedback object for each question-answer pair
                            feedback = Feedback(
                                student=student,
                                question=question,
                                answer=answer,
                                comment=comment,  # Use the new comment
                                is_active=True
                            )
                            feedback.save()
                            saved_count += 1
                            print(f"✓ Saved updated feedback #{saved_count}: Q{question_id} → A{answer_id}")
                            
                        except FeedbackQuestion.DoesNotExist:
                            print(f"✗ Error: Question {question_id} not found or inactive")
                            continue
                        except FeedbackAnswer.DoesNotExist:
                            print(f"✗ Error: Answer {answer_id} not found or inactive")
                            continue
                        except Exception as e:
                            print(f"✗ Error saving feedback for Q{question_id}: {e}")
                            continue
            
            print(f"Successfully saved {saved_count} updated feedback responses")
            return saved_count > 0  # Return True if at least one feedback was saved
            
        except Exception as e:
            print(f"Error in process_feedback_data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        print("POST data:", dict(self.request.POST))
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("masters:feedback_list")


class FeedbackDeleteView(mixins.HybridDeleteView):
    model = Feedback
    permissions = ("is_superuser","admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")



class FeedbackReportView(mixins.HybridListView):
    model = Feedback
    template_name = "masters/feedback/feedback_report.html"
    permissions = ("branch_staff", "admin_staff", "is_superuser", "ceo", "cfo", "coo", "hr", "cmo", "mentor")

    def get_queryset(self):
        return Feedback.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filters from GET
        branch_id = self.request.GET.get('branch')  # branch filter (optional)
        employee_type = self.request.GET.get('employee_type', 'all')  # 'faculty', 'fao', 'all' (default 'all')

        # Base feedback queryset filtered by branch (student's branch)
        feedback_qs = Feedback.objects.filter(is_active=True).select_related(
            'student', 'question', 'answer', 'student__branch', 'student__course'
        )
        if branch_id:
            feedback_qs = feedback_qs.filter(student__branch_id=branch_id)

        # Available branches and the dropdown options now reflect feedback type choices
        context['branches'] = Branch.objects.filter(is_active=True)
        # Use feedback type keys (faculty/fao) as filter values
        context['employee_types'] = [
            ('all', 'All Feedback Types'),
            ('faculty', 'Faculty'),
            ('fao', 'Front Office (FAO)'),
        ]
        context['selected_branch'] = branch_id
        context['selected_employee_type'] = employee_type

        # Overall stats (based on filtered feedback_qs)
        total_feedbacks = feedback_qs.count()
        total_students = feedback_qs.values('student').distinct().count()
        overall_avg_rating = feedback_qs.aggregate(avg_rating=Avg('answer__answer_value'))['avg_rating'] or 0

        # Decide which sections to show
        show_teacher = employee_type in (None, '', 'all', 'faculty')
        show_fao = employee_type in (None, '', 'all', 'fao')

        # Compute stats (only compute what we'll show)
        teacher_stats = self.get_teacher_stats(feedback_qs, branch_id) if show_teacher else []
        fao_stats = self.get_fao_stats(feedback_qs, branch_id) if show_fao else []

        staff_type_stats = self.get_staff_type_stats(teacher_stats, fao_stats, total_students)
        total_staff = len(teacher_stats) + len(fao_stats)
        feedback_type_stats = self.get_feedback_type_stats(feedback_qs)
        answer_distribution = self.get_answer_distribution(feedback_qs, total_feedbacks)
        recent_feedbacks = feedback_qs.order_by('-created')[:10]

        # Prepare JSON-ready chart data for JS
        teacher_chart_data = []
        for stat in teacher_stats:
            teacher_chart_data.append({
                'id': getattr(stat['employee'], 'id', None),
                'name': stat['name'],
                'course': getattr(stat['employee'].course, 'name', '-') if getattr(stat['employee'], 'course_id', None) else '-',
                'branch': getattr(stat['employee'].branch, 'name', '-') if getattr(stat['employee'], 'branch_id', None) else '-',
                'total_feedbacks': stat['total_feedbacks'],
                'ratings': [
                    stat['rating_1'],
                    stat['rating_2'],
                    stat['rating_3'],
                    stat['rating_4'],
                    stat['rating_5'],
                ]
            })

        fao_chart_data = []
        for stat in fao_stats:
            fao_chart_data.append({
                'id': getattr(stat['employee'], 'id', None),
                'name': stat['name'],
                'branch': getattr(stat['employee'].branch, 'name', '-') if getattr(stat['employee'], 'branch_id', None) else '-',
                'total_feedbacks': stat['total_feedbacks'],
                'ratings': [
                    stat['rating_1'],
                    stat['rating_2'],
                    stat['rating_3'],
                    stat['rating_4'],
                    stat['rating_5'],
                ]
            })

        context.update({
            'total_feedbacks': total_feedbacks,
            'total_students': total_students,
            'total_staff': total_staff,
            'overall_avg_rating': overall_avg_rating,
            'staff_type_stats': staff_type_stats,
            'teacher_stats': teacher_stats,
            'fao_stats': fao_stats,
            'feedback_type_stats': feedback_type_stats,
            'answer_distribution': answer_distribution,
            'recent_feedbacks': recent_feedbacks,
            'teacher_chart_data': teacher_chart_data,
            'fao_chart_data': fao_chart_data,
            'show_teacher': show_teacher,
            'show_fao': show_fao,
            'title': 'Staff Feedback Analytics Report',
            'is_feedback_report': True,
        })

        return context

    def get_feedback_type_stats(self, feedback_qs):
        type_data = feedback_qs.values('question__feedback_type').annotate(
            total_feedbacks=Count('id'),
            avg_rating=Avg('answer__answer_value')
        ).order_by('question__feedback_type')

        feedback_type_stats = []
        for stat in type_data:
            feedback_type_stats.append({
                'type': stat['question__feedback_type'],
                'total_feedbacks': stat['total_feedbacks'],
                'avg_rating': stat['avg_rating'] or 0
            })
        return feedback_type_stats

    def get_answer_distribution(self, feedback_qs, total_feedbacks):
        answers_data = feedback_qs.values('answer__answer_value', 'answer__answer').annotate(count=Count('id')).order_by('answer__answer_value')
        answer_distribution = []
        for rating in range(1, 6):
            rating_data = next((item for item in answers_data if item['answer__answer_value'] == rating), None)
            if rating_data:
                percentage = (rating_data['count'] / total_feedbacks * 100) if total_feedbacks > 0 else 0
                answer_distribution.append({
                    'value': rating,
                    'answer': rating_data['answer__answer'],
                    'count': rating_data['count'],
                    'percentage': percentage
                })
            else:
                answer_distribution.append({
                    'value': rating,
                    'answer': f'{rating} Star{"s" if rating > 1 else ""}',
                    'count': 0,
                    'percentage': 0.0
                })
        return answer_distribution

    def get_teacher_stats(self, feedback_qs, branch_id):
        """
        Teachers are determined by Employee with usertype 'teacher'.
        Feedback considered: question__feedback_type == 'faculty' and student.course == teacher.course
        """
        teachers = Employee.objects.filter(user__usertype='teacher', is_active=True)
        if branch_id:
            teachers = teachers.filter(branch_id=branch_id)

        stats = []
        for teacher in teachers:
            teacher_feedback = feedback_qs.filter(
                question__feedback_type='faculty',
                student__course_id=teacher.course_id
            )
            # If you need teacher branch match, enable below:
            # if teacher.branch_id:
            #     teacher_feedback = teacher_feedback.filter(student__branch_id=teacher.branch_id)

            agg = teacher_feedback.aggregate(
                total_feedbacks=Count('id'),
                total_students=Count('student', distinct=True),
                avg_rating=Avg('answer__answer_value'),
                rating_1=Count('id', filter=Q(answer__answer_value=1)),
                rating_2=Count('id', filter=Q(answer__answer_value=2)),
                rating_3=Count('id', filter=Q(answer__answer_value=3)),
                rating_4=Count('id', filter=Q(answer__answer_value=4)),
                rating_5=Count('id', filter=Q(answer__answer_value=5))
            )

            stats.append({
                'employee': teacher,
                'name': teacher.fullname() if hasattr(teacher, 'fullname') else str(teacher),
                'total_feedbacks': agg['total_feedbacks'] or 0,
                'total_students': agg['total_students'] or 0,
                'avg_rating': agg['avg_rating'] or 0,
                'rating_1': agg['rating_1'] or 0,
                'rating_2': agg['rating_2'] or 0,
                'rating_3': agg['rating_3'] or 0,
                'rating_4': agg['rating_4'] or 0,
                'rating_5': agg['rating_5'] or 0,
            })
        return stats

    def get_fao_stats(self, feedback_qs, branch_id):
        """
        FAO staff usertype 'fao'.
        Feedback considered: question__feedback_type == 'fao' and student.branch == fao.branch
        """
        fao_staff = Employee.objects.filter(user__usertype='fao', is_active=True)
        if branch_id:
            fao_staff = fao_staff.filter(branch_id=branch_id)

        stats = []
        for fao in fao_staff:
            fao_feedback = feedback_qs.filter(
                question__feedback_type='fao',
                student__branch_id=fao.branch_id
            )
            agg = fao_feedback.aggregate(
                total_feedbacks=Count('id'),
                total_students=Count('student', distinct=True),
                avg_rating=Avg('answer__answer_value'),
                rating_1=Count('id', filter=Q(answer__answer_value=1)),
                rating_2=Count('id', filter=Q(answer__answer_value=2)),
                rating_3=Count('id', filter=Q(answer__answer_value=3)),
                rating_4=Count('id', filter=Q(answer__answer_value=4)),
                rating_5=Count('id', filter=Q(answer__answer_value=5))
            )

            stats.append({
                'employee': fao,
                'name': fao.get_full_name() if hasattr(fao, 'get_full_name') else str(fao),
                'total_feedbacks': agg['total_feedbacks'] or 0,
                'total_students': agg['total_students'] or 0,
                'avg_rating': agg['avg_rating'] or 0,
                'rating_1': agg['rating_1'] or 0,
                'rating_2': agg['rating_2'] or 0,
                'rating_3': agg['rating_3'] or 0,
                'rating_4': agg['rating_4'] or 0,
                'rating_5': agg['rating_5'] or 0,
            })
        return stats

    def get_staff_type_stats(self, teacher_stats, fao_stats, total_students):
        staff_type_stats = []

        teacher_total_feedbacks = sum(stat['total_feedbacks'] for stat in teacher_stats)
        teacher_total_students = sum(stat['total_students'] for stat in teacher_stats)
        teacher_avg_rating = 0
        if teacher_total_feedbacks > 0:
            teacher_avg_rating = sum(stat['avg_rating'] * stat['total_feedbacks'] for stat in teacher_stats) / teacher_total_feedbacks
        teacher_response_rate = (teacher_total_students / total_students * 100) if total_students > 0 else 0

        staff_type_stats.append({
            'staff_type': 'teacher',
            'total_staff': len(teacher_stats),
            'total_feedbacks': teacher_total_feedbacks,
            'total_students': teacher_total_students,
            'avg_rating': teacher_avg_rating,
            'response_rate': teacher_response_rate
        })

        fao_total_feedbacks = sum(stat['total_feedbacks'] for stat in fao_stats)
        fao_total_students = sum(stat['total_students'] for stat in fao_stats)
        fao_avg_rating = 0
        if fao_total_feedbacks > 0:
            fao_avg_rating = sum(stat['avg_rating'] * stat['total_feedbacks'] for stat in fao_stats) / fao_total_feedbacks
        fao_response_rate = (fao_total_students / total_students * 100) if total_students > 0 else 0

        staff_type_stats.append({
            'staff_type': 'fao',
            'total_staff': len(fao_stats),
            'total_feedbacks': fao_total_feedbacks,
            'total_students': fao_total_students,
            'avg_rating': fao_avg_rating,
            'response_rate': fao_response_rate
        })

        return staff_type_stats
    

class PlacementReportView(mixins.HybridListView):
    model = Admission
    template_name = "masters/placement/placement_report.html"
    context_object_name = 'students'
    filterset_fields = ['branch', 'course', 'batch', 'stage_status']
    
    def get_queryset(self):
        allowed_statuses = ['completed', 'internship', 'placed']
        user = self.request.user

        queryset = Admission.objects.select_related(
            'batch', 'course', 'branch'
        )

        if user.usertype == "teacher" and hasattr(user, 'employee'):
            if user.employee.branch:
                queryset = queryset.filter(branch=user.employee.branch)

            if user.employee.course:
                queryset = queryset.filter(course=user.employee.course)

        
        branch_id = self.request.GET.get('branch')
        course_id = self.request.GET.get('course')
        batch_id = self.request.GET.get('batch')
        status = self.request.GET.get('status')

        if status:
            queryset = queryset.filter(stage_status=status)
        else:
            queryset = queryset.filter(stage_status__in=allowed_statuses)

        if branch_id and user.usertype != "teacher":
            queryset = queryset.filter(branch_id=branch_id)

        if course_id and user.usertype != "teacher":
            queryset = queryset.filter(course_id=course_id)

        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        branch_id = self.request.GET.get('branch')
        course_id = self.request.GET.get('course')
        batch_id = self.request.GET.get('batch')
        status = self.request.GET.get('status')

        context['is_teacher'] = False
        context['teacher_branch_id'] = None
        context['teacher_course_id'] = None

        if user.usertype == "teacher" and hasattr(user, 'employee'):
            context['is_teacher'] = True
            context['teacher_branch_id'] = (
                str(user.employee.branch.id) if user.employee.branch else None
            )
            context['teacher_course_id'] = (
                str(user.employee.course.id) if user.employee.course else None
            )

            branch_id = branch_id or context['teacher_branch_id']
            course_id = course_id or context['teacher_course_id']

        context['branches'] = Branch.objects.filter(is_active=True)
        context['courses'] = Course.objects.filter(is_active=True)

        context['placement_statuses'] = [
            ('completed', "Course Completed"),
            ('internship', "On Internship"),
            ('placed', "Placed")
        ]

        batches = Batch.objects.filter(is_active=True)
        if branch_id:
            batches = batches.filter(branch_id=branch_id)
        if course_id:
            batches = batches.filter(course_id=course_id)

        context['batches'] = batches

        context['selected_branch'] = branch_id
        context['selected_course'] = course_id
        context['selected_batch'] = batch_id
        context['selected_status'] = status

        context['total_students'] = Admission.objects.count()
        context['eligible_students'] = Admission.objects.filter(
            stage_status__in=['completed', 'internship', 'placed']
        ).count()

        context['filters_applied'] = any(
            x in self.request.GET for x in ['branch', 'course', 'batch', 'status']
        )

        return context
    

class StudentPlacementHistoryView(mixins.HybridDetailView):
    template_name = "masters/placement/student_placement_history.html"
    model = Admission
    context_object_name = 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        context['placement_histories'] = PlacementHistory.objects.filter(student=student)
        return context
    

class PlacementHistoryCreateView(mixins.HybridCreateView):
    model = PlacementHistory
    form_class = forms.PlacementHistoryForm

    def get_student(self):
        return get_object_or_404(Admission, pk=self.kwargs['student_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['student'] = self.get_student()
        return kwargs

    def form_valid(self, form):
        form.instance.student = self.get_student()  # assign Admission instance, not string
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.get_student()
        return context

    def get_success_url(self):
        return reverse_lazy(
            "masters:student_placement_history",
            kwargs={"pk": self.kwargs['student_id']}
        )

class PlacementHistoryUpdateView(mixins.HybridUpdateView):
    model = PlacementHistory
    fields = [
        'company_name', 'designation', 'interview_type', 
        'interview_date', 'interview_status', 'attended_status',
        'joining_status', 'joining_date'
    ]
    
    def get_success_url(self):
        return reverse_lazy("masters:student_placement_history", kwargs={"pk": self.object.student.pk})


class PlacementHistoryDeleteView(mixins.HybridDeleteView):
    model = PlacementHistory
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class PublicMessageListView(mixins.HybridListView):
    model = PublicMessage
    table_class = tables.PublicMessageTable
    filterset_fields = {'message': ['exact'], }
    permissions = ("branch_staff", "teacher", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "tele_caller", "sales_head", "mentor")
    branch_filter = False
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_public_message"] = True 
        context["is_master"] = True
        context["title"] = "Public Message"
        return context
    

class PublicMessageDetailView(mixins.HybridDetailView):
    model = PublicMessage
    permissions = ("branch_staff","admin_staff", "teacher", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "masters/public_message/public_message_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_public_message"] = True
        context["is_master"] = True
        context["title"] = "Public Message"
        return context
    
    
class PublicMessageCreateView(mixins.HybridCreateView):
    model = PublicMessage
    permissions = ("is_superuser", "teacher", "branch_staff", "mentor",)
    form_class = forms.PublicMessageForm
    template_name = "masters/public_message/public_message_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "New Public Message"
        return context

    def form_valid(self, form):
        """
        Save the form and send WhatsApp messages to filtered admissions
        """
        # Set creator
        form.instance.creator = self.request.user
        
        # Save the instance first to get an ID
        self.object = form.save()
        
        # Send WhatsApp messages in background
        import threading
        thread = threading.Thread(target=self.send_messages_in_background)
        thread.daemon = True
        thread.start()
        
        # Handle AJAX response
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            object_data = model_to_dict(self.object)
            object_data.setdefault('name', str(self.object))
            return JsonResponse({'success': True, 'result': object_data})
        
        return HttpResponseRedirect(self.get_success_url())

    def send_messages_in_background(self):
        """
        Send messages in background thread to avoid blocking the request
        """
        try:
            # Refresh the object from database to ensure we have latest data
            obj = PublicMessage.objects.get(pk=self.object.pk)
            result = obj.send_whatsapp_messages()
            print(f"Message sending completed: {result}")
            
            # You can add success message or logging here
            messages.success(self.request, f"Messages sent successfully! Sent: {result['sent_count']}, Failed: {result['failed_count']}")
            
        except Exception as e:
            print(f"Error sending messages: {e}")
            messages.error(self.request, f"Error sending messages: {str(e)}")

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)


class PublicMessageUpdateView(mixins.HybridUpdateView):
    model = PublicMessage
    fields = "__all__"
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "masters/public_message/public_message_update.html"

    def form_valid(self, form):
        """
        Save the form and send WhatsApp messages if not already sent or message changed
        """
        # Check if message content changed or not sent before
        message_changed = 'message' in form.changed_data
        filter_changed = any(field in form.changed_data for field in ['message_type', 'filter_type', 'branch', 'course'])
        
        response = super().form_valid(form)
        
        # Send messages only if not sent before or if message/filter was modified
        if not self.object.sent or message_changed or filter_changed:
            import threading
            thread = threading.Thread(target=self.send_messages_in_background)
            thread.daemon = True
            thread.start()
        
        return response

    def send_messages_in_background(self):
        """
        Send messages in background thread
        """
        try:
            # Refresh the object from database to ensure we have latest data
            obj = PublicMessage.objects.get(pk=self.object.pk)
            result = obj.send_whatsapp_messages()
            print(f"Message sending completed: {result}")
            
            # You can add success message or logging here
            messages.success(self.request, f"Messages sent successfully! Sent: {result['sent_count']}, Failed: {result['failed_count']}")
            
        except Exception as e:
            print(f"Error sending messages: {e}")
            messages.error(self.request, f"Error sending messages: {str(e)}")

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)


class PublicMessageUpdateView(mixins.HybridUpdateView):
    model = PublicMessage
    form_class = forms.PublicMessageForm
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "masters/public_message/public_message_update.html"

    def form_valid(self, form):
        """
        Save the form and send WhatsApp messages if not already sent or message changed
        """
        # Check if message content changed or not sent before
        message_changed = 'message' in form.changed_data
        filter_changed = any(field in form.changed_data for field in ['message_type', 'filter_type', 'branch', 'course'])
        
        response = super().form_valid(form)
        
        # Send messages only if not sent before or if message/filter was modified
        if not self.object.sent or message_changed or filter_changed:
            import threading
            thread = threading.Thread(target=self.send_messages_in_background)
            thread.daemon = True
            thread.start()
        
        return response

    def send_messages_in_background(self):
        """
        Send messages in background thread
        """
        try:
            # Refresh the object from database to ensure we have latest data
            from .models import PublicMessage
            obj = PublicMessage.objects.get(pk=self.object.pk)
            result = obj.send_whatsapp_messages()
            print(f"Message sending completed: {result}")
            
            # You can add success message or logging here
            messages.success(self.request, f"Messages sent successfully! Sent: {result['sent_count']}, Failed: {result['failed_count']}")
            
        except Exception as e:
            print(f"Error sending messages: {e}")
            messages.error(self.request, f"Error sending messages: {str(e)}")


class PublicMessageDeleteView(mixins.HybridDeleteView):
    model = PublicMessage
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class HolidayListView(mixins.HybridListView):
    model = Holiday
    table_class = tables.HolidayTable
    filterset_fields = {'name': ['exact'], "scope": ['exact'], "date": ['exact']}
    permissions = ("admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor",)
    branch_filter = False
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_holiday"] = True 
        context["is_master"] = True
        context["title"] = "Holidays"
        context["can_add"] = True
        context["new_link"] = reverse_lazy("masters:holiday_create")    
        return context
    

class HolidayDetailView(mixins.HybridDetailView):
    model = Holiday
    permissions = ("admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_holiday"] = True
        context["is_master"] = True
        context["title"] = "Holiday"
        return context
    

class HolidayCreateView(mixins.HybridCreateView):
    model = Holiday
    permissions = ("admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor",)
    form_class = forms.HolidayForm
    template_name = "masters/holiday/holiday_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "New Holiday"  
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            form.instance.creator = self.request.user
            
            self.object = form.save(commit=False)
            self.object.save()

            if self.object.scope == "all":
                branches_qs = Branch.objects.filter(is_active=True)
                
                branches_to_set = [
                    branch for branch in branches_qs
                    if not AttendanceRegister.objects.filter(branch=branch, date=self.object.date).exists()
                ]
                self.object.branch.set(branches_to_set)

            else:
                selected_branches = form.cleaned_data.get('branch')
                
                branches_to_set = [
                    branch for branch in selected_branches
                    if not AttendanceRegister.objects.filter(branch=branch, date=self.object.date).exists()
                ]
                
                self.object.branch.set(branches_to_set)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)
    

class HolidayUpdateView(mixins.HybridUpdateView):
    model = Holiday
    form_class = forms.HolidayForm
    permissions = ("admin_staff", "is_superuser", "ceo", "cfo", "coo", "hr", "cmo", "mentor",)
    template_name = "masters/holiday/holiday_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Edit Holiday"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.save()

            if self.object.scope == "all":
                target_branches = Branch.objects.filter(is_active=True)
            else:
                target_branches = form.cleaned_data.get('branch')

            branches_to_set = []
            if target_branches:
                for branch in target_branches:
                    has_attendance = AttendanceRegister.objects.filter(
                        branch=branch, 
                        date=self.object.date
                    ).exists()
                    
                    if not has_attendance:
                        branches_to_set.append(branch)

            self.object.branch.set(branches_to_set)

        return HttpResponseRedirect(self.get_success_url())


class HolidayDeleteView(mixins.HybridDeleteView):
    model = Holiday
    permissions = ("admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor",)


class HeroBannerListView(mixins.HybridListView):
    model = HeroBanner
    table_class = tables.HeroBannerTable
    filterset_fields = {'banner_type': ['exact'],}
    permissions = ("branch_staff", "teacher", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "tele_caller", "sales_head", "mentor")
    branch_filter = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hero Banners"
        context['is_master'] = True 
        context['can_add'] = True
        context["is_hero_banner"] = True
        return context
    

class HeroBannerDetailView(mixins.HybridDetailView):
    model = HeroBanner
    permissions = ("branch_staff", "admin_staff", "teacher", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")


class HeroBannerCreateView(mixins.HybridCreateView):
    model = HeroBanner
    permissions = ("branch_staff", "admin_staff", "teacher", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "New Hero Banner"
        return context

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

    
class HeroBannerUpdateView(mixins.HybridUpdateView):
    model = HeroBanner
    fields = "__all__"
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class HeroBannerDeleteView(mixins.HybridDeleteView):
    model = HeroBanner
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class EventView(mixins.HybridTemplateView):
    model = Event
    permissions = (
        "branch_staff", "partner", "teacher", "student", "is_superuser", 
        "ceo", "cfo", "coo", "hr", "cmo", "tele_caller", "sales_head", "mentor"
    )
    template_name = "masters/event/event_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["title"] = "Events"
        context["is_master"] = True
        context["can_add"] = True
        context["is_events"] = True

        events = Event.objects.filter(is_active=True)

        if user.usertype == "teacher":
            events = events.filter(event_type__in=["teacher", "all"])
            events = events.filter(
                Q(branch__isnull=True) | Q(branch=user.employee.branch)
            ).filter(
                Q(course__isnull=True) | Q(course=user.employee.course)
            ).distinct()

        elif user.usertype == "student":
            events = events.filter(event_type__in=["student", "all"])
            events = events.filter(
                Q(branch__isnull=True) | Q(branch=user.student.branch)
            ).filter(
                Q(course__isnull=True) | Q(course=user.student.course)
            ).distinct()

        elif user.usertype in ["admin_staff", "is_superuser", "ceo", "cfo", "coo", "hr", "cmo"] or user.is_superuser:
            events = events.filter(is_active=True) 

        else:
            events = events.filter(
                Q(branch__isnull=True) | Q(branch=user.branch)
            ).distinct()

        context["events"] = events
        return context
    

class EventListView(mixins.HybridListView):
    model = Event
    permissions = ("branch_staff", "teacher", "student", "admin_staff", "is_superuser", "ceo","cfo","coo","hr","cmo", "tele_caller", "sales_head", "mentor")
    table_class = tables.EventTable
    filterset_fields = {'event_type': ['exact'], 'filter_type': ['exact']}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Events"
        context['is_master'] = True 
        context['can_add'] = True
        context["is_event_list"] = True
        return context
    

class EventDetailView(mixins.HybridDetailView):
    model = Event
    permissions = ("branch_staff", "admin_staff", "teacher", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")


class EventCreateView(mixins.HybridCreateView):
    model = Event
    permissions = ("branch_staff", "admin_staff", "teacher", "is_superuser", "ceo","cfo","coo","hr","cmo", "mentor")
    form_class = forms.EventForm
    template_name = "masters/event/event_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "New Event"
        return context

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)


    
class EventUpdateView(mixins.HybridUpdateView):
    model = Event
    form_class = forms.EventForm
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "masters/event/event_form.html"


class EventDeleteView(mixins.HybridDeleteView):
    model = Event
    permissions = ("is_superuser","admin_staff", "teacher", "branch_staff", "ceo","cfo","coo","hr","cmo", "mentor")
