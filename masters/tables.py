from django.urls import reverse_lazy
from core.base import BaseTable
from django.utils.html import format_html
from django_tables2 import columns
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.template.defaultfilters import truncatechars
from admission .models import Admission
from employees .models import Employee
from core.choices import LEAVE_STATUS_CHOICES
from .models import Activity, Batch, BranchActivity, Course, Feedback, FeedbackAnswer, FeedbackQuestion, HeroBanner, Holiday, LeaveRequest, PDFBookResource, PdfBook, ComplaintRegistration, ChatSession, PublicMessage, Syllabus, SyllabusMaster, Update, PlacementRequest, RequestSubmission, Event


class BatchTable(BaseTable):
    created = None
    class Meta(BaseTable.Meta):
        model = Batch
        fields = ("branch", "batch_name", "course", "starting_date", "ending_date", "starting_time", "ending_time", "status" )
        
    
class CourseTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="btn-group" role="group">
            <a href="{{ record.get_absolute_url }}" 
               class="btn btn-sm btn-outline-primary me-1">
                <i class="fe fe-file"></i> Open
            </a>
            
            {% if record.brochure %}
            <!-- View Brochure Button -->
            <a href="{{ record.brochure.url }}" 
               class="btn btn-sm btn-outline-info me-1" 
               target="_blank">
                <i class="fe fe-eye"></i> View Brochure
            </a>

            <div class="btn-group me-1" role="group">
                <button type="button" 
                        class="btn btn-sm btn-outline-success dropdown-toggle" 
                        data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="fe fe-share-2"></i> Share
                </button>
                <ul class="dropdown-menu">
                    <li>
                        <a class="dropdown-item" 
                           href="https://api.whatsapp.com/send?text={{ request.scheme }}://{{ request.get_host }}{{ record.brochure.url }}" 
                           target="_blank">
                            <i class="fab fa-whatsapp text-success"></i> WhatsApp
                        </a>
                    </li>
                    <li>
                        <a class="dropdown-item" 
                           href="https://www.facebook.com/sharer/sharer.php?u={{ request.scheme }}://{{ request.get_host }}{{ record.brochure.url }}" 
                           target="_blank">
                            <i class="fab fa-facebook text-primary"></i> Facebook
                        </a>
                    </li>
                    <li>
                        <a class="dropdown-item" 
                           href="https://www.instagram.com/?url={{ request.scheme }}://{{ request.get_host }}{{ record.brochure.url }}" 
                           target="_blank">
                            <i class="fab fa-instagram text-danger"></i> Instagram
                        </a>
                    </li>
                    <li>
                        <a class="dropdown-item" href="#" 
                           onclick="copyBrochureLink('{{ request.scheme }}://{{ request.get_host }}{{ record.brochure.url }}')">
                            <i class="fe fe-copy"></i> Copy Link
                        </a>
                    </li>
                </ul>
            </div>
            {% endif %}
            
            <a href="{% url 'masters:course_syllabus_list' pk=record.pk %}" 
               class="btn btn-sm btn-outline-warning">
                <i class="fe fe-list"></i> Syllabus
            </a>
        </div>
        """,
        orderable=False,
    )

    class Meta(BaseTable.Meta):
        model = Course
        fields = ("name", )


class PDFBookResourceTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="btn-group">
            <a class="btn btn-default mx-1 btn-sm" title='View' href="{{record.get_absolute_url}}"><i class="fa fa-eye"></i></a>
            <a class="btn btn-default mx-1 btn-sm" title='Edit' href="{{record.get_update_url}}"><i class="fa fa-edit"></i></a>
            <a class="btn btn-default mx-1 btn-sm" title='Delete' href="{{record.get_delete_url}}"><i class="fa fa-trash"></i></a>
        </div>
        """,
        orderable=False,
    )
    class Meta(BaseTable.Meta):
        model = PDFBookResource
        fields = ("course", )
        
    
class PdfBookTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="btn-group">
            <a href="{{ record.pdf.url }}" class="btn btn-sm btn-light btn-outline-info">OPEN</a>
        </div>
        """,
        orderable=False,
    )
    class Meta(BaseTable.Meta):
        model = PdfBook
        fields = ("name", "pdf", "created", "action")
    

class SyllabusMasterTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = SyllabusMaster
        fields = ("course", "month", "week")


class SyllabusTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = Syllabus
        fields = ("syllabus_master", "order_id", "title",)


class SyllabusBatchTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="btn-group">
            <a class="btn btn-default mx-1 btn-sm" title='View' href="{% url 'masters:syllabus_report_detail' course_pk=record.course.pk batch_pk=record.pk %}"><i class="fa fa-eye"></i></a>
        </div>
        """,
        orderable=False,
    )

    class Meta(BaseTable.Meta):
        model = Batch
        fields = ("branch", "batch_name", "course",)
        attrs = {"class": "table table-striped table-bordered"}


class ComplaintTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="btn-group">
            <a class="btn btn-default mx-1 btn-sm" title='View' href="{{record.get_absolute_url}}"><i class="fa fa-eye"></i></a>
            <a class="btn btn-default mx-1 btn-sm" title='Edit' href="{{record.get_update_url}}"><i class="fa fa-edit"></i></a>
            <a class="btn btn-default mx-1 btn-sm" title='Delete' href="{{record.get_delete_url}}"><i class="fa fa-trash"></i></a>
        </div>
        """,
        orderable=False,
    )

    # Full name using TemplateColumn
    creator_full_name = columns.TemplateColumn(
        "{{ record.creator.first_name }} {{ record.creator.last_name }}",
        verbose_name="Full Name"
    )

    # Branch and user type
    creator_branch = columns.Column(accessor='creator.branch', verbose_name='Branch')
    creator_usertype = columns.Column(accessor='creator.usertype', verbose_name='User Type')

    # Status with colored badges
    status = columns.TemplateColumn(
        """
        {% if record.status == "Complaint Registered" %}
            <span class="badge bg-primary">{{ record.status }}</span>
        {% elif record.status == "In Progress" %}
            <span class="badge bg-warning text-white">{{ record.status }}</span>
        {% elif record.status == "Resolved" %}
            <span class="badge bg-success">{{ record.status }}</span>
        {% elif record.status == "Closed" %}
            <span class="badge bg-danger">{{ record.status }}</span>
        {% else %}
            <span class="badge bg-secondary">{{ record.status }}</span>
        {% endif %}
        """,
        verbose_name="Status",
        orderable=True,
        attrs={"td": {"class": "text-center"}}
    )

    class Meta(BaseTable.Meta):
        model = ComplaintRegistration
        fields = (
            "creator_full_name",
            "creator_branch",
            "creator_usertype",
            "complaint_type",
            "status",
            "created",
        )
        attrs = {"class": "table table-striped table-bordered"}

    
class ChatSessionTable(BaseTable):
    action = columns.TemplateColumn(
        template_code="""
        {% if record.user and record.user.id %}
            <a href="{% url 'masters:student_chat' record.user.id %}" class="btn msg-btn btn-sm btn-primary position-relative">
                <i class="fas fa-comments fa-2x"></i>
                {% if record.unread_count > 0 %}
                    <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                        {{ record.unread_count }}
                    </span>
                {% endif %}
            </a>
        {% else %}
            <span class="text-muted">No user assigned</span>
        {% endif %}
        """,
        orderable=False,
        verbose_name="Chat"
    )

    class Meta(BaseTable.Meta):
        model = Admission
        fields = ("admission_number", "fullname", "user", "course", 'batch')
        attrs = {"class": "table table-striped table-bordered"}

    
class EmployeeChatSessionTable(BaseTable):
    action = columns.TemplateColumn(
        template_code="""
        {% if record.user and record.user.id %}
            <a href="{% url 'masters:student_chat' record.user.id %}" class="btn msg-btn btn-sm btn-primary position-relative">
                <i class="fas fa-comments fa-2x"></i>
                {% if record.unread_count %}
                    <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                        {{ record.unread_count }}
                    </span>
                {% endif %}
            </a>
        {% else %}
            <span class="text-muted">No user assigned</span>
        {% endif %}
        """,
        orderable=False,
        verbose_name="Chat"
    )
    user__usertype = columns.Column(
        accessor="user.usertype",
        verbose_name="User Type",
    )
    fullname = columns.Column(
        accessor="fullname",
        verbose_name="Full Name",
    )
    created = None

    class Meta(BaseTable.Meta):
        model = Employee
        fields = ("employee_id", "fullname", "personal_email", "user__usertype")
        attrs = {"class": "table table-striped table-bordered"}

    
class UpdateTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="btn-group">
            <a class="btn btn-default mx-1 btn-sm" title='View' href="{{record.get_absolute_url}}"><i class="fa fa-eye"></i></a>
            <a class="btn btn-default mx-1 btn-sm" title='Edit' href="{{record.get_update_url}}"><i class="fa fa-edit"></i></a>
            <a class="btn btn-default mx-1 btn-sm" title='Delete' href="{{record.get_delete_url}}"><i class="fa fa-trash"></i></a>
        </div>
        """,
        orderable=False,
    )
    class Meta(BaseTable.Meta):
        model = Update
        fields = ("title", )
        attrs = {"class": "table table-striped table-bordered"}

    
class PlacementRequestTable(BaseTable):
    student__admission_number = columns.Column(
        accessor="student.admission_number",
        verbose_name="Admission Number",
    )

    student__course = columns.Column(
        accessor="student.course",
        verbose_name="Course",
    )

    student__batch = columns.Column(
        accessor="student.batch",
        verbose_name="Batch",
    )

    student__age = columns.Column(
        accessor="student.age",
        verbose_name="Age",
        attrs={"td": {"style": "font-weight: bold;"}},
    )

    status = columns.Column(
        empty_values=(),
        verbose_name="Status",
        orderable=False,
    )

    def render_status(self, record):
        url = reverse_lazy("masters:placement_request_status_update", args=[record.pk])

        options = ""
        for key, label in PlacementRequest._meta.get_field("status").choices:
            selected = "selected" if record.status == key else ""
            options += f'<option value="{key}" {selected}>{label}</option>'

        return mark_safe(
            f"""
            <select class="form-control status-change"
                    data-url="{url}">
                {options}
            </select>
            """
        )

    class Meta(BaseTable.Meta):
        model = PlacementRequest
        fields = (
            "student__admission_number",
            "student",
            "student__age",
            "student__course",
            "student__batch",
            "status",
        )
        attrs = {"class": "table table-striped table-bordered"}

    
class ActivityTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = Activity
        fields = ("name", "description")
        attrs = {"class": "table table-striped table-bordered"}

    
class BranchActivityTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = BranchActivity
        fields = ("activity", "branch", "point")
        attrs = {"class": "table table-striped table-bordered"}
        

def get_row_class(record, table):
    request = getattr(table, "request", None)
    if not request or request.user.usertype != "hr":
        return ""  

    latest_hr_history = record.status_history.filter(
        usertype="hr"
    ).order_by("-date").first()
    
    if latest_hr_history and latest_hr_history.next_usertype and latest_hr_history.next_usertype != "hr":
        hr_status = latest_hr_history.status
        if hr_status == "approved":
            return "table-success-transparent"
        elif hr_status == "rejected":
            return "table-danger-transparent"

    reviewer_history = record.status_history.exclude(
        usertype__in=["hr", "branch_staff"]
    ).order_by("-date").first()
    reviewer_status = reviewer_status = reviewer_history.status if reviewer_history else None

    creator_usertype = getattr(getattr(record, "creator", None), "usertype", None)

    hr_assigned_to_creator = False
    if creator_usertype:
        hr_assigned_to_creator = record.status_history.filter(
            usertype="hr",
            next_usertype=creator_usertype
        ).exists()

    if reviewer_status in ["approved", "rejected"]:
        if hr_assigned_to_creator:
            if reviewer_status == "approved":
                return "table-success-transparent"
            else: 
                return "table-danger-transparent"
        else:
            return "table-warning-transparent"

    return ""

class RequestSubmissionTable(BaseTable):
    created = columns.DateTimeColumn(verbose_name="Created At", format="d/m/Y")
    request_id = columns.Column(verbose_name="Request ID")
    status = columns.TemplateColumn(
        verbose_name="Status",
        template_code="""
            {% if record.status == "approved" %}
                <span class="badge bg-success">Approved</span>
            {% elif record.status == "rejected" %}
                <span class="badge bg-danger">Rejected</span>
            {% elif record.status == "re_assign" %}
                <span class="badge bg-dark bg-gradient">Re Assigned</span>
            {% elif request.user.usertype == "branch_staff" %}
                <span class="badge bg-warning text-white">Pending</span>
            {% elif record.approved_or_rejected_for_current_user|default_if_none:False %}
                {% if record.status == "approved" %}
                    <span class="badge bg-success">Approved</span>
                {% elif record.status == "rejected" %}
                    <span class="badge bg-danger">Rejected</span>
                {% endif %}
            {% elif record.status == "processing" or record.is_processing %}
                <span class="badge bg-primary text-white">Processing</span>
            {% else %}
                <span class="badge bg-warning text-white">Pending</span>
            {% endif %}
        """,
        orderable=True,
    )
    
    is_request_completed = columns.TemplateColumn(
        """
            {% if record.is_request_completed == "true" %}
                <span class="badge bg-success">Completed</span>
            {% else %}
                <span class="badge bg-warning text-white">Pending</span>
            {% endif %}
        """,
        orderable=True,
    )

    class Meta:
        model = RequestSubmission
        fields = ("request_id", "title", "branch_staff", "created", "status", "is_request_completed")
        attrs = {"class": "table key-buttons table-bordered border-bottom"}
        row_attrs = {
            "class": lambda record, table: get_row_class(record, table)
        }


    
class MyRequestSubmissionTable(BaseTable):
    created = columns.DateTimeColumn(verbose_name="Created At", format="d/m/Y")
    request_id = columns.Column(verbose_name="Request ID")
    status = columns.TemplateColumn(
        verbose_name="Status",
        template_code="""
            {% if record.hr_assigned_to_creator %}
                {% if record.status == 'approved' %}
                    <span class="badge bg-success">Approved</span>
                {% elif record.status == 'rejected' %}
                    <span class="badge bg-danger">Rejected</span>
                {% else %}
                    <span class="badge bg-primary text-white">Processing</span>
                {% endif %}
            {% else %}
                <span class="badge bg-warning text-white">Pending</span>
            {% endif %}
        """,
        orderable=True,
    )

    class Meta:
        model = RequestSubmission
        fields = ("request_id", "title", "branch_staff", "created", "status")
        attrs = {"class": "table key-buttons border-bottom"}


class LeaveRequestTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="d-flex text-start">
            {% if record.status == "pending" and request.user.usertype == "teacher" or request.user.usertype == "mentor" and record.status == "pending"  %}
                <a href="javascript:void(0);" class="action-btns1 approve-btn" data-id="{{ record.pk }}" data-action="approved">
                    <i class="fe fe-check text-success"></i>
                </a>

                <a href="javascript:void(0);" class="action-btns1 reject-btn" data-id="{{ record.pk }}" data-action="rejected">
                    <i class="fe fe-x text-danger"></i>
                </a>
            {% endif %}

            <a href="{{ record.get_absolute_url }}" class="action-btns1" title="View">
                <i class="fe fe-eye text-primary"></i>
            </a>
            {% if request.user.usertype == record.permission_users %}
                <a href="{{ record.get_delete_url }}" class="action-btns1" data-bs-toggle="tooltip" data-bs-placement="top" aria-label="Delete" data-bs-original-title="Delete">
                    <i class="fe fe-trash-2 text-danger"></i>
                </a>
            {% endif %}
        </div>
        """,
        orderable=False,
    )

    class Meta(BaseTable.Meta):
        model = LeaveRequest
        fields = ("student", "student__branch", "student__course", "subject", "start_date", "end_date", "status", "created")
        attrs = {"class": "table table-striped table-bordered"}

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
        }

        config = status_map.get(key, {
            "css": "badge badge-secondary text-bg-secondary",
            "style": "background:#6c757d;color:#fff",
        })

        label = dict(LEAVE_STATUS_CHOICES).get(value, value or "")

        return format_html(
            '<span class="{}" style="padding:0.275rem 0.65rem;{}">{}</span>',
            config["css"],
            config["style"],
            label,
        )


class FeedbackTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <a href="{{ record.get_absolute_url }}" class="btn btn-sm btn-light btn-outline-info">OPEN</a>
        """,
        orderable=False,
    )
    class Meta(BaseTable.Meta):
        model = Feedback
        fields = ("student", "rating", "comments",)
        attrs = {"class": "table table-striped table-bordered"}

    
class FeedbackQuestionTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = FeedbackQuestion
        fields = ("feedback_type", "question",)
        attrs = {"class": "table table-striped table-bordered"}

    
class FeedbackAnswerTable(BaseTable):
    created = None
    class Meta(BaseTable.Meta):
        model = FeedbackAnswer
        fields = ("question", "rating", "feedback")
        attrs = {"class": "table table-striped table-bordered"}

    
class CourseSyllabusMasterTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <div class="btn-group">
            <a class="btn btn-default mx-1 btn-sm" title='View' href="{% url 'masters:course_syllabus_list' record.pk %}"><i class="fa fa-eye"></i></a>
        </div>
        """,
        orderable=False,
    )
    class Meta(BaseTable.Meta):
        model = Course
        fields = ("name", "created", )

    
class PublicMessageTable(BaseTable):
    message = columns.Column(verbose_name="Message")

    def render_message(self, value):
        # Truncate to 200 characters
        truncated = truncatechars(value, 200)
        # Mark safe so HTML renders
        return mark_safe(truncated)

    class Meta(BaseTable.Meta):
        model = PublicMessage
        fields = ("message", "created")
        attrs = {"class": "table table-striped table-bordered"}

    
class HolidayTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = Holiday
        fields = ("name", "date", "scope", "branch")
        attrs = {"class": "table table-striped table-bordered"}

    
class HeroBannerTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = HeroBanner
        fields = ("banner_type", "image",)
        attrs = {"class": "table table-striped table-bordered"}

    
class EventTable(BaseTable):
    class Meta(BaseTable.Meta):
        model = Event
        fields = ("title", "event_type", "filter_type", )
        attrs = {"class": "table table-striped table-bordered"}