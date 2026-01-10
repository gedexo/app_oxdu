from core.base import BaseTable, CustomBaseTable
import django_tables2 as tables
from django.utils.safestring import mark_safe 
from django_tables2 import columns
from django.utils.html import format_html
from django.utils import timezone

from .models import Admission, AttendanceRegister, FeeReceipt, AdmissionEnquiry, FeeStructure
from core.choices import STUDENT_STAGE_STATUS_CHOICES


class AdmissionTable(BaseTable):
    created = None
    fullname = columns.Column(verbose_name="Student", order_by="first_name")
    course = columns.Column(verbose_name="Course")
    contact_number = columns.Column(verbose_name="Mob")
    admission_date = columns.Column(verbose_name="Admission Date")
    admission_number = columns.Column(verbose_name="Ad.No", linkify=True)
    
    stage_status = tables.TemplateColumn(
        template_code="""
            <select class="form-select form-select-sm stage-select"
                    style="min-width: 140px;"
                    data-id="{{ record.id }}"
                    data-current="{{ record.stage_status }}">
                {% for value, label in status_choices %}
                    <option value="{{ value }}"
                        {% if record.stage_status == value %}selected{% endif %}>
                        {{ label }}
                    </option>
                {% endfor %}
            </select>
        """,
        verbose_name="Stage",
        orderable=False,
        extra_context={
            "status_choices": STUDENT_STAGE_STATUS_CHOICES
        }
    )

    action = tables.TemplateColumn(
        template_code="""
            <div class="d-flex justify-content-center gap-2">

                <a href="{{ record.get_absolute_url }}" class="btn btn-sm btn-outline-success" title="Open Profile">
                    <i class="fe fe-eye"></i>
                </a>

                {% if request.user.usertype != 'student' %}
                <a href="{{ record.get_student_syllabus_report_url }}" target="_blank"
                class="btn btn-sm btn-outline-warning" title="Syllabus Report">
                    <i class="fe fe-file-text"></i>
                </a>
                {% endif %}

                {% if not record.user %}
                    <a type="button" class="btn btn-sm btn-outline-danger"
                    title="Error: No User Linked"
                    onclick="showWarningModal(
                            'Missing User Account',
                            'This admission record is not linked to any User account. The student cannot login or access the system.'
                    )">
                        <i class="fe fe-alert-triangle"></i>
                    </a>

                {% elif not record.user.branch %}
                    <a type="button" class="btn btn-sm btn-outline-danger"
                    title="Error: Branch Not Assigned"
                    onclick="showWarningModal(
                            'Branch Missing',
                            'The linked User account exists but does not have a Branch assigned.'
                    )">
                        <i class="fe fe-alert-triangle"></i>
                    </a>
                {% endif %}

                <a href="{% url 'admission:student_fee_overview_detail' record.pk %}"
                class="btn btn-sm btn-outline-primary" target="_blank" title="Fee Overview">
                    <i class="fe fe-bar-chart-2"></i>
                </a>

                {% if request.user.usertype != 'student' %}
                <a href="{% url 'admission:student_certificate' record.pk %}"
                class="btn btn-sm btn-outline-info" target="_blank" title="Certificates">
                    <i class="fe fe-award"></i>
                </a>
                {% endif %}

            </div>
        """,
        orderable=False,
        verbose_name="Action",
    )

    def render_course(self, value):
        """
        Customize the course name display.
        """
        if value and value.name == "Graphic Designing":
            return "GD"
        elif value and value.name == "Digital Marketing":
            return "DM"
        else:
            return value.name if value else "-"
    
    latest_remark = tables.TemplateColumn(
        template_code="""
        {% with record.get_latest_stage_remark as latest_remark %}
            <a class="text-center d-flex align-items-center justify-content-center" 
            type="button" 
            onclick="showRemark('{{ record.id }}', '{{ record.fullname|escapejs }}')"
            title="View History">
                {% if latest_remark %}
                    <i class="fe fe-alert-circle text-theme" style="font-size: 1.2rem;"></i>
                {% else %}
                    <i class="fe fe-clock text-muted" style="font-size: 1.2rem;"></i>
                {% endif %}
            </a>
        {% endwith %}
        """,
        orderable=False,
        verbose_name="Remark"
    )
    
    id_card = tables.TemplateColumn(
        template_code="""
            <a href="{{ record.get_id_card_absolute_url }}"
            class="btn btn-sm btn-outline-info"
            title="Download ID Card"
            target="_blank">
                <i class="fe fe-credit-card"></i>
            </a>
        """,
        verbose_name="ID Card",
        orderable=False
    )

    profile = tables.TemplateColumn(
        template_code="""
            <a href="{% url 'admission:admission_profile_detail' record.pk %}"
            class="btn btn-sm btn-outline-secondary"
            title="View Profile"
            target="_blank">
               <i class="fa-regular fa-address-card"></i>
            </a>
        """,
        verbose_name="Profile",
        orderable=False
    )
    
    fee_progress = tables.TemplateColumn(
        template_code="""
        {% with record.get_fee_progress_data as fee %}
        <div class="fee-progress-wrapper" style="min-width: 120px;">
            <div class="d-flex justify-content-between mb-1">
                <small class="fw-bold text-{{ fee.color }}">{{ fee.percent }}%</small>
                <small class="text-muted" style="font-size: 10px;">{{ fee.paid|floatformat:0 }}/{{ fee.total|floatformat:0 }}</small>
            </div>
            <div class="progress progress-xs mb-0">
                <div class="progress-bar bg-{{ fee.color }}" 
                     role="progressbar" 
                     style="width: {{ fee.percent }}%" 
                     aria-valuenow="{{ fee.percent }}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                </div>
            </div>
        </div>
        {% endwith %}
        """,
        verbose_name="Fee Progress",
        orderable=False
    )
    
    class Meta:
        model = Admission
        fields = (
            "admission_number", "admission_date", "fullname", "personal_email", 
            "contact_number", "branch", "course", "batch_type", "fee_progress", 
            "stage_status", "course_mode", "user__is_active", "action", 
            "profile", "id_card", "latest_remark"
        )
        attrs = {"class": "table star-student table-hover table-bordered"}
        row_attrs = {
            "class": lambda record: "inactive-student-row" if (not record.is_active or record.stage_status != 'active') else ""
        }
        

class AdmissionEnquiryTable(BaseTable):
    full_name = columns.Column(verbose_name="Student")
    course = columns.Column(verbose_name="Course")
    contact_number = columns.TemplateColumn(
        verbose_name="Mob",
        template_code='<a href="tel:{{ record.contact_number }}">{{ record.contact_number }}</a>',
        orderable=False
    )
    date = columns.Column(verbose_name="Enquiry Date")
    status = columns.Column(verbose_name="Enquiry Status")
    action = tables.TemplateColumn(
        verbose_name='Action',
        template_code='''
            <a href="{{ record.get_absolute_url }}" class="btn btn-sm btn-primary">View</a>
            <a href="{{ record.get_update_url }}" class="btn btn-sm btn-warning">Edit</a>
        ''',
        orderable=False
    )
    created = None

    class Meta:
        model = AdmissionEnquiry
        fields = ("date", "full_name", "course", "contact_number", "tele_caller", "enquiry_type", "status", "action")
        attrs = {"class": "table star-student table-hover table-bordered"}

    
class PublicEnquiryListTable(CustomBaseTable):
    full_name = columns.Column(verbose_name="Full Name")
    contact_number = columns.Column(verbose_name="Contact Number")

    tele_caller_column = tables.TemplateColumn(
        template_code='''
            {% if record.tele_caller %}
                <strong>{{ record.tele_caller.user.get_full_name }}</strong>
            {% elif not table.request.user.usertype == "sales_head" %}
                <span class="text-danger">Not Assigned</span>
            {% endif %}

            {% if table.request.user.usertype == "sales_head" %}
                <select name="tele_caller"
                        class="form-select form-select-sm mt-2 bulk-assign-tele-caller"
                        data-record-id="{{ record.id }}">
                    <option value="">-- Assign Tele Caller --</option>
                    {% for caller in tele_callers %}
                        <option value="{{ caller.id }}">{{ caller.user.get_full_name }}</option>
                    {% endfor %}
                </select>
            {% endif %}
        ''',
        verbose_name='Tele Caller',
        orderable=False,
    )

    action = tables.TemplateColumn(
        template_code='''
            {% if record.tele_caller %}
                <span class="badge bg-success">Assigned</span>
            {% elif table.request.user.usertype == "tele_caller" or table.request.user.employee.is_also_tele_caller == "Yes" %}
                <a href="{% url 'admission:add_to_me' record.id %}" class="btn btn-sm btn-danger fw-bold">ADD TO ME</a>
            {% else %}
                <span class="badge bg-danger text-white">Not Assigned</span>
            {% endif %}
        ''',
        verbose_name='Action',
        orderable=False,
    )

    def render_contact_number(self, value):
        return f"**** **** {value[-4:]}" if value else ""

    class Meta:
        model = AdmissionEnquiry
        fields = ("full_name", "contact_number", "city", "enquiry_type", "tele_caller_column", "created",)
        sequence = ("selection", "...", "action")
        attrs = {"class": "table star-student table-hover table-bordered"}
    

class AttendanceRegisterTable(BaseTable):
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
    created = None
    class Meta:
        model = AttendanceRegister
        fields = ("batch", "course", "date", "action")
        attrs = {"class": "table key-buttons border-bottom table-hover table-bordered"}
        
    
class FeeReceiptTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <a href="{{ record.get_absolute_url }}" class="btn btn-sm btn-light btn-outline-info">OPEN</a>
        {% if table.request.user.is_superuser or table.request.user.usertype in "admin_staff,ceo,cfo,coo,hr,cmo" %}
            <a href="{{ record.get_update_url }}" class="btn btn-sm btn-light btn-outline-warning">EDIT</a>
            <a href="{{ record.get_delete_url }}" class="btn btn-sm btn-light btn-outline-danger">DELETE</a>
        {% endif %}
        """,
        orderable=False,
    )
    
    payment_type = columns.Column(empty_values=(), orderable=False, verbose_name="Payment Type")
    amount = columns.TemplateColumn(
        template_code="""
        {% load humanize %}
        <span class="text-success fw-bold fs-6">₹{{ record.get_amount|floatformat:2|intcomma }}</span>
        """,
        orderable=False,
        verbose_name="Amount"
    )
    
    def render_payment_type(self, value, record):
        payment_types = record.get_payment_types()
        if payment_types:
            return ", ".join(payment_types)
        return "-"
    
    created = None

    class Meta:
        model = FeeReceipt
        fields = ("student", "receipt_no", "date", "payment_type", "amount", "action")
        attrs = {"class": "table key-buttons border-bottom table-hover table-bordered"}
        

class StudentFeeOverviewTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <a href="{{ record.get_fee_overview_absolute_url }}" class="btn btn-sm btn-light btn-outline-info">OPEN</a>
        """,
        orderable=False,
    )   
    created = None
    fullname = columns.Column(verbose_name="Student", order_by="Student")
    contact_number = columns.Column(verbose_name="Mob")
    admission_date = columns.Column(verbose_name="Admission Date")
    admission_number = columns.Column(verbose_name="Ad.No", linkify=True)
    course = columns.Column(verbose_name="Course")
    course__fees = columns.Column(verbose_name="Course Fees")
    get_total_fee_amount = columns.Column(verbose_name="Total Receipt", orderable=False)
    get_balance_amount = columns.Column(verbose_name="Balance Due", orderable=False)

    def render_course(self, value):
        """
        Customize the course name display.
        """
        if value and value.name == "Graphic Designing":
            return "GD"
        elif value and value.name == "Digital Marketing":
            return "DM"
        else:
            # Show original name if it exists, else show "-"
            return value.name if value else "-"

    def render_branch(self, value):
        if value and value.name == "Kondotty":
            return "KDY"
        elif value and value.name == "Calicut":
            return "CLT"
        elif value and value.name == "Perinthalmanna":
            return "PMNA"
        elif value and value.name == "Kochi":
            return "Kochi"

    def render_course__fees(self, value):
        return format_html('<span class="fw-bold">₹{}</span>', value)
    
    def render_get_total_fee_amount(self, value):
        return format_html('<span class="fw-bold text-success">₹{}</span>', value)

    def render_get_balance_amount(self, value):
        return format_html('<span class="fw-bold text-danger">₹{}</span>', value)

    fee_progress = tables.TemplateColumn(
        template_code="""
        {% with record.get_fee_progress_data as fee %}
        <div class="fee-progress-wrapper" style="min-width: 120px;">
            <div class="d-flex justify-content-between mb-1">
                <small class="fw-bold text-{{ fee.color }}">{{ fee.percent }}%</small>
                <small class="text-muted" style="font-size: 10px;">{{ fee.paid|floatformat:0 }}/{{ fee.total|floatformat:0 }}</small>
            </div>
            <div class="progress progress-xs mb-0">
                <div class="progress-bar bg-{{ fee.color }}" 
                     role="progressbar" 
                     style="width: {{ fee.percent }}%" 
                     aria-valuenow="{{ fee.percent }}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                </div>
            </div>
        </div>
        {% endwith %}
        """,
        verbose_name="Fee Progress",
        orderable=False
    )
    
    class Meta:
        model = Admission
        fields = (
            "fullname", "contact_number", "admission_date", 
            "admission_number", "course", "branch",  "fee_progress", "course__fees", 
            "get_total_fee_amount", "get_balance_amount", "action"
        )
        attrs = {
            "class": "table key-buttons border-bottom table-hover table-bordered"
        }
        row_attrs = {
            "class": lambda record: (
                "fee-cleared-row"
                if record.get_balance_amount() == 0
                else "fee-danger-row"
                if not FeeStructure.objects.filter(student=record).exists()
                else ""
            )
        }



class DueStudentsTable(BaseTable):
    action = columns.TemplateColumn(
        """
        <a href="{% url 'admission:student_fee_overview_detail' record.student.id %}" class="btn btn-sm btn-light btn-outline-info">OPEN</a>
        """,
        orderable=False,
    )
    created = None
    student__contact_number = columns.Column(verbose_name="Mob")
    student__admission_date = columns.DateColumn(verbose_name="Admission Date", format="d/m/Y")
    payment_date = columns.DateColumn(verbose_name="Payment Date", format="d/m/Y")
    
    # Use TemplateColumn for remaining_amount to use template filters directly
    remaining_amount = columns.TemplateColumn(
        """
        {% load humanize %}
        <span class="fw-bold text-danger">₹ {{ value|floatformat:2|intcomma }}</span>
        """,
        verbose_name="Due Amount"
    )
    
    due_date = columns.DateColumn(verbose_name="Due Date", format="d/m/Y")

    def render_due_date(self, value):
        if value:
            today = timezone.now().date()
            if value < today:
                # Overdue - red color
                return format_html('<span class="fw-bold text-danger">{}</span>', value.strftime("%d/%m/%Y"))
            else:
                # Not yet due - orange color
                return format_html('<span class="fw-bold text-warning">{}</span>', value.strftime("%d/%m/%Y"))
        return "-"

    def render_payment_date(self, value):
        if value:
            return format_html('<span class="fw-bold">{}</span>', value.strftime("%d/%m/%Y"))
        return "-"

    def render_student(self, value):
        if value:
            return format_html('<strong>{}</strong>', value.fullname())
        return "-"

    def render_student__course(self, value):
        if value:
            if value.name == "Graphic Designing":
                return format_html('<span class="badge bg-info">GD</span>')
            elif value.name == "Digital Marketing":
                return format_html('<span class="badge bg-primary">DM</span>')
            else:
                return format_html('<span class="badge bg-secondary">{}</span>', value.name)
        return "-"

    class Meta:
        model = FeeStructure
        fields = (
            "student", "student__contact_number", "student__admission_date",
            "student__admission_number", "student__course",
            "payment_date", "due_date", "remaining_amount", "action"
        )
        attrs = {
            "class": "table key-buttons border-bottom table-hover table-bordered"
        }
