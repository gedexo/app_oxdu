import io
import calendar
from django.template import context
from django.utils import timezone
from datetime import datetime
from weasyprint import HTML, CSS
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.core.cache import cache
from django.templatetags.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.utils.timezone import now
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from core import mixins
from core.utils import build_url
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from decimal import Decimal
from django.views.decorators.http import require_POST

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password


from . import forms
from . import tables
from core import choices
from .functions import generate_employee_id
from .models import Department, Partner
from .models import Designation
from .models import Employee, Payroll, PayrollPayment, AdvancePayrollPayment, EmployeeLeaveRequest, EmployeeLeaveBalance
from branches.models import Branch


def get_employee_salary(request, pk):
    try:
        employee = Employee.objects.get(pk=pk)
        data = {
            "basic_salary": str(employee.basic_salary or 0.00),
            "hra": str(employee.hra or 0.00),
            "other_allowance": str(employee.other_allowance or 0.00),
            "transportation_allowance": str(employee.transportation_allowance or 0.00),
            "total_salary": str(employee.total_salary),
        }
        return JsonResponse(data)
    except Employee.DoesNotExist:
        return JsonResponse({"error": "Employee not found"}, status=404)
        
    
def ajax_get_employee_payrolls(request):
    employee_id = request.GET.get("employee_id")
    payrolls = []

    if employee_id:
        qs = Payroll.objects.filter(
            employee_id=employee_id,
            is_active=True
        ).values(
            "id",
            "payroll_year",
            "payroll_month",
            "employee__first_name",
            "employee__last_name",
            "basic_salary"
        )


        payrolls = [
            {
                **p,
                "employee_name": f"{p['employee__first_name']} {p['employee__last_name'] or ''}".strip(),
                "basic_salary": float(p["basic_salary"]),
                "remaining_salary": float(Payroll.objects.get(id=p["id"]).remaining_salary),
                "status": Payroll.objects.get(id=p["id"]).status
            }
            for p in qs
        ]

        print("Filtered Payrolls:", payrolls)
    else:
        print("⚠️ No employee_id provided")

    return JsonResponse({"payrolls": payrolls})


def get_employee_payroll_data(request):
    employee_id = request.GET.get('employee_id')
    year = request.GET.get('year')
    month = request.GET.get('month')

    if not all([employee_id, year, month]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        employee = Employee.objects.get(id=employee_id)
        year = int(year)
        month = int(month)

        # 1. Determine month boundaries
        month_start = datetime(year, month, 1).date()
        last_day = calendar.monthrange(year, month)[1]
        month_end = datetime(year, month, last_day).date()

        # 2. Fetch approved leaves overlapping with this month
        leaves = EmployeeLeaveRequest.objects.filter(
            employee=employee,
            status='approved',
            start_date__lte=month_end,
            end_date__gte=month_start
        )

        total_leave_days = 0
        for leave in leaves:
            # Only count days that fall inside the selected month
            actual_start = max(leave.start_date, month_start)
            actual_end = min(leave.end_date, month_end)
            days = (actual_end - actual_start).days + 1
            total_leave_days += days

        # 3. Apply the "1 Paid Leave" rule
        paid_leaves_allowed = 1
        # Unpaid absences = total leaves minus 1 (but not less than 0)
        unpaid_absences = max(0, total_leave_days - paid_leaves_allowed)

        # 4. Calculate current allowances from employee profile
        allowances = (employee.hra or 0) + (employee.other_allowance or 0) + (employee.transportation_allowance or 0)

        return JsonResponse({
            'basic_salary': float(employee.basic_salary or 0),
            'allowances': float(allowances),
            'total_leaves': total_leave_days,
            'paid_leaves': min(total_leave_days, paid_leaves_allowed),
            'unpaid_absences': unpaid_absences,
        })
    except (Employee.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid data'}, status=400)


@login_required
@require_POST
def update_leave_status(request, pk):
    leave = get_object_or_404(EmployeeLeaveRequest, pk=pk)
    
    # Permission Check
    if not (request.user.is_superuser or request.user.is_staff or request.user.groups.filter(name='hr').exists()):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    status = request.POST.get('status')
    if status in ['approved', 'rejected']:
        leave.status = status
        if status == 'approved':
            leave.approved_by = getattr(request.user, 'employee', None)
            leave.approved_date = timezone.now()
        leave.save()
        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False, "error": "Invalid Status"})


def ajax_get_employee_payroll_data(request):
    employee_id = request.GET.get('employee_id')
    year = request.GET.get('year')
    month = request.GET.get('month')

    if not (employee_id and year and month):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        employee = Employee.objects.get(id=employee_id)
        
        # 1. Get Basic Salary & Allowances
        basic_salary = employee.basic_salary or 0
        allowances = (employee.hra or 0) + (employee.other_allowance or 0) + (employee.transportation_allowance or 0)

        # 2. Get Leave Balance Info
        balance, _ = EmployeeLeaveBalance.objects.get_or_create(employee=employee)
        
        # Logic: Limit = Min(CarryForward, 6) + 1 (Current Month)
        limit_paid = min(balance.paid_carry_forward, balance.CARRY_LIMIT_PAID) + balance.MONTHLY_PAID
        limit_wfh = min(balance.wfh_carry_forward, balance.CARRY_LIMIT_WFH) + balance.MONTHLY_WFH

        # 3. Get Actual Leaves Taken in this specific Month/Year
        leaves_qs = EmployeeLeaveRequest.objects.filter(
            employee=employee,
            status='approved',
            start_date__year=year,
            start_date__month=month
        )

        taken_paid = 0.0
        taken_wfh = 0.0

        for leave in leaves_qs:
            if leave.leave_type == 'wfh':
                taken_wfh += leave.total_days
            else:
                taken_paid += leave.total_days

        # 4. Calculate Excess (Unpaid)
        unpaid_paid = max(0.0, taken_paid - limit_paid)
        unpaid_wfh = max(0.0, taken_wfh - limit_wfh)
        total_unpaid = unpaid_paid + unpaid_wfh

        # Prepare Data for Table
        leave_data = {
            'paid_leave': {
                'carry': balance.paid_carry_forward,
                'monthly': balance.MONTHLY_PAID,
                'total_limit': limit_paid,
                'taken': taken_paid,
                'unpaid': unpaid_paid
            },
            'wfh': {
                'carry': balance.wfh_carry_forward,
                'monthly': balance.MONTHLY_WFH,
                'total_limit': limit_wfh,
                'taken': taken_wfh,
                'unpaid': unpaid_wfh
            }
        }

        return JsonResponse({
            'basic_salary': float(basic_salary),
            'allowances': float(allowances),
            'total_unpaid_days': float(total_unpaid),
            'leave_breakdown': leave_data
        })

    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)


def employee_appointment(request, pk):
    instance = get_object_or_404(Employee, pk=pk)
    
    cache_key = f'employee_appointment_pdf_{pk}'
    
    pdf_file = cache.get(cache_key)
    
    if not pdf_file:
        base_url = request.build_absolute_uri('/')
        
        context = {
            "instance": instance,
            "page_1_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_1.png')),
            "page_2_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_2.png')),
            "page_3_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_3.png')),
            "page_4_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_4.png')),
            "page_5_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_5.png')),
            "page_6_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_6.png')),
            "page_7_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_7.png')),
            "page_8_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_8.png')),
        }

        html_string = render_to_string(
            'employees/employee/appointment/employee_appointment.html',
            context
        )
        
        html = HTML(string=html_string, base_url=base_url)

        pdf_file = html.write_pdf(stylesheets=[
            CSS(string='''
                @page {
                    size: A4;
                    margin: 0mm;
                }
                body {
                    margin: 0;
                    padding: 0;
                }
            ''')
        ])
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, pdf_file, 3600)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="employee_appointment_{instance.pk}.pdf"'
    return response

from django.views.decorators.http import require_POST
import logging
logger = logging.getLogger(__name__)

@login_required
@require_POST
def share_employee_appointment(request, pk):
    instance = get_object_or_404(Employee, pk=pk)
    
    # Check if employee has an email
    if not instance.personal_email:
        return JsonResponse({
            'success': False,
            'message': '❌ Employee email not found! Please add an email address first.'
        })
    
    # Check if already sent
    if instance.is_appointment_letter_sent:
        return JsonResponse({
            'success': False,
            'message': '⚠️ Appointment letter has already been sent to this employee.'
        })
    
    try:
        # Generate PDF (reuse from cache if available)
        cache_key = f'employee_appointment_pdf_{pk}'
        pdf_file = cache.get(cache_key)
        
        if not pdf_file:
            base_url = request.build_absolute_uri('/')
            
            context = {
                "instance": instance,
                "page_1_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_1.png')),
                "page_2_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_2.png')),
                "page_3_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_3.png')),
                "page_4_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_4.png')),
                "page_5_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_5.png')),
                "page_6_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_6.png')),
                "page_7_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_7.png')),
                "page_8_image": request.build_absolute_uri(static('app/assets/images/employee_appointment/page_8.png')),
            }

            html_string = render_to_string(
                'employees/employee/appointment/employee_appointment.html',
                context
            )
            
            html = HTML(string=html_string, base_url=base_url)

            pdf_file = html.write_pdf(stylesheets=[
                CSS(string='''
                    @page {
                        size: A4;
                        margin: 0mm;
                    }
                    body {
                        margin: 0;
                        padding: 0;
                    }
                ''')
            ])
            
            # Cache for 1 hour
            cache.set(cache_key, pdf_file, 3600)
        
        # Get employee name
        employee_name = instance.get_full_name() if hasattr(instance, 'get_full_name') else str(instance)
        
        # Company and date info
        current_year = datetime.now().year
        current_date = datetime.now().strftime('%B %d, %Y')
        
        # Email context for HTML template
        email_context = {
            'employee_name': employee_name,
            'employee': instance,
            'current_year': current_year,
            'current_date': current_date,
        }
        
        # Render HTML email
        html_content = render_to_string(
            'employees/employee/appointment/email/appointment_letter_email.html',
            email_context
        )
        
        # Plain text version (simple and professional)
        text_content = f"""OXDU Integrated Media School
Human Resources Department

{current_date}

{employee_name}
{instance.personal_email}

Re: Letter of Appointment

Dear {employee_name},

We are pleased to confirm your appointment with OXDU Integrated Media School. We believe that your skills and experience will be a valuable asset to our organization.

Please find attached your official Letter of Appointment, which outlines the terms and conditions of your employment, including:

• Position title and job responsibilities
• Compensation and benefits package
• Employment terms and conditions
• Start date and reporting structure

We request you to carefully review the attached document. Should you have any questions or require any clarification regarding the terms of your appointment, please feel free to contact us.

We look forward to welcoming you to the OXDU family and are confident that this will be the beginning of a mutually rewarding association.

Warm regards,

Human Resources Department
OXDU Integrated Media School

---
Note: This is an automatically generated email. Please do not reply to this message. For any queries, please contact our HR department directly.

© {current_year} OXDU Integrated Media School. All rights reserved.
"""
        
        # Email subject
        subject = 'Letter of Appointment - OXDU Integrated Media School'
        
        # From email - OXDU HR Department
        from_email = 'OXDU HR Department <{}>'.format(
            getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        )
        
        # Create email with both HTML and plain text
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content.strip(),
            from_email=from_email,
            to=[instance.personal_email],
            reply_to=[getattr(settings, 'HR_EMAIL', settings.EMAIL_HOST_USER)],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Attach PDF
        email.attach(
            f'Appointment_Letter_{employee_name.replace(" ", "_")}.pdf',
            pdf_file,
            'application/pdf'
        )
        
        # Send email via Brevo SMTP
        email.send(fail_silently=False)
        
        # Update the boolean field
        instance.is_appointment_letter_sent = True
        if hasattr(instance, 'appointment_letter_sent_at'):
            instance.appointment_letter_sent_at = timezone.now()
            instance.save(update_fields=['is_appointment_letter_sent', 'appointment_letter_sent_at'])
        else:
            instance.save(update_fields=['is_appointment_letter_sent'])
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Appointment letter sent successfully to <strong>{instance.personal_email}</strong>'
        })
        
    except Exception as e:
        logger.error(f"Error sending appointment letter to {instance.personal_email}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'❌ Error sending email: {str(e)}'
        })
    

class DepartmentListView(mixins.HybridListView):
    model = Department
    table_class = tables.DepartmentTable
    filterset_fields = {"name": ["icontains"]}
    permissions = ("branch_staff", "partner", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_master'] = True
        context["is_department"] = True
        return context


class DepartmentDetailView(mixins.HybridDetailView):
    model = Department
    permissions = ("branch_staff", "partner", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_delete"] = mixins.check_access(self.request, ("branch_staff"))
        return context


class DepartmentCreateView(mixins.HybridCreateView):
    model = Department
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False


class DepartmentUpdateView(mixins.HybridUpdateView):
    model = Department
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False


class DepartmentDeleteView(mixins.HybridDeleteView):
    model = Department
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False


class DesignationListView(mixins.HybridListView):
    model = Designation
    table_class = tables.DesignationTable
    branch_filter = None
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_master'] = True
        context["is_designation"] = True
        return context


class DesignationDetailView(mixins.HybridDetailView):
    model = Designation
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class DesignationCreateView(mixins.HybridCreateView):
    model = Designation
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class DesignationUpdateView(mixins.HybridUpdateView):
    model = Designation
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class DesignationDeleteView(mixins.HybridDeleteView):
    model = Designation
    permissions = ("branch_staff", "admin_staff", "ceo","cfo","coo","hr","cmo", "mentor")


class ProfileView(mixins.HybridView):
    template_name = "employees/profile.html"

    def get(self, request, *args, **kwargs):
        # Check if this is an AJAX request for a form section
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'section' in kwargs:
            return self.get_edit_section(request, kwargs['section'])
            
        employee = get_object_or_404(Employee, user=request.user)
        context = {
            "title": "Profile",
            "is_profile": True,
            "employee": employee, 
            "photo_form": forms.EmployeePhotoForm()
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        employee = get_object_or_404(Employee, user=request.user)

        # Check if it's an AJAX request for form submission
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Handle photo upload (separate from section updates)
            if 'photo' in request.FILES:
                form = forms.EmployeePhotoForm(
                    request.POST or None,
                    request.FILES or None,
                    instance=employee
                )
                if form.is_valid():
                    form.save()
                    return JsonResponse({"status": True})
                
                # Print form errors to terminal
                print("Photo form errors:")
                for field, errors in form.errors.items():
                    print(f"  {field}: {errors}")
                
                return JsonResponse({"status": False, "errors": form.errors})

            # Handle section updates
            section = request.POST.get('section')
            if not section:
                return JsonResponse({"status": False, "error": "No section specified"})

            # Handle different form types
            if section == 'personal':
                form = forms.EmployeePersonalDataForm(request.POST, instance=employee)
            elif section == 'parent':
                form = forms.EmployeeParentDataForm(request.POST, instance=employee)
            elif section == 'address':
                form = forms.EmployeeAddressDataForm(request.POST, instance=employee)
            elif section == 'financial':
                form = forms.EmployeeFinancialDataForm(request.POST, instance=employee)
            elif section == 'documents':
                form = forms.EmployeeDocumentsForm(request.POST, request.FILES, instance=employee)
                if form.is_valid():
                    instance = form.save(commit=False)
                    if 'aadhar' in request.FILES:
                        employee.aadhar = request.FILES['aadhar']
                    if 'pancard' in request.FILES:
                        employee.pancard = request.FILES['pancard']
                    employee.save(update_fields=['aadhar', 'pancard'])
                    return JsonResponse({"status": True})
            else:
                return JsonResponse({"status": False, "error": "Invalid section"})

            if hasattr(form, 'fields') and 'is_active' in form.fields:
                form.fields.pop('is_active', None)

            if form.is_valid():
                if section == 'documents':
                    instance = form.save(commit=False)
                    # Only update the document fields, not the required ones that aren't in the form
                    for field in request.FILES:
                        setattr(instance, field, request.FILES[field])
                    for field in request.POST:
                        if field in ['aadhar', 'pancard', 'offer_letter', 'joining_letter', 'agreement_letter', 'experience_letter']:
                            setattr(instance, field, request.POST[field])
                    instance.save()
                else:
                    form.save()
                return JsonResponse({"status": True})
            
            # Print form errors to terminal
            print(f"Form errors for section '{section}':")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
            
            # Also print non-field errors if any
            if form.non_field_errors():
                print(f"  Non-field errors: {form.non_field_errors()}")
            
            # Return detailed form errors
            return JsonResponse({"status": False, "errors": form.errors})

        # Handle non-AJAX requests if needed
        return JsonResponse({"status": False, "error": "Invalid request"})

    def get_edit_section(self, request, section):
        employee = get_object_or_404(Employee, user=request.user)

        if section == 'personal':
            form = forms.EmployeePersonalDataForm(instance=employee)
        elif section == 'parent':
            form = forms.EmployeeParentDataForm(instance=employee)
        elif section == 'address':
            form = forms.EmployeeAddressDataForm(instance=employee)
        elif section == 'financial':
            form = forms.EmployeeFinancialDataForm(instance=employee)
        elif section == 'documents':
            form = forms.EmployeeOfficialDataForm(instance=employee)
        else:
            return JsonResponse({"error": "Invalid section"}, status=400)

        form_html = render_to_string('employees/partials/edit_form.html', {
            'form': form,
            'section': section
        })
        return HttpResponse(form_html)


class EmployeeListView(mixins.HybridListView):
    template_name = "employees/employee/employee_list.html"
    model = Employee
    table_class = tables.EmployeeTable
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")
    filterset_fields = {'branch': ['exact'] ,'department': ['exact'], 'designation': ['exact'], 'gender': ['exact'], 'employment_type': ['exact'], 'status':['exact']}
    search_fields = ("user__email", "employee_id", "first_name", "last_name", "marital_status", "mobile", "whatsapp")
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user 
        
        if user.is_superuser:
            pass
        elif hasattr(user, "usertype") and user.usertype == "branch_staff":
            employee = Employee.objects.filter(user=user).first()
            if employee and employee.branch:
                queryset = queryset.filter(branch=employee.branch)
        
        return queryset.filter(is_active=True, status="Appointed")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()  # This has search and filters applied
        
        # Calculate stats for cards using the FILTERED queryset
        active_employees = queryset.filter(is_active=True, status="Appointed")
        permanent_employees = queryset.filter(is_active=True, status="Appointed", employment_type="PERMANENT")
        total_employees = queryset.filter(is_active=True)
        total_salary = sum([emp.total_salary for emp in queryset if emp.total_salary])
        active_employees_total_salary = sum(
            [emp.total_salary for emp in permanent_employees if emp.total_salary]
        )
        
        employment_type_counts = {
            key: queryset.filter(employment_type=key).count()
            for key, _ in choices.EMPLOYMENT_TYPE_CHOICES
        }
        employment_type_salary = {
            key: queryset.filter(
                employment_type=key, is_active=True, status="Appointed"
            ).aggregate(total=Sum("basic_salary"))["total"] or 0
            for key, _ in choices.EMPLOYMENT_TYPE_CHOICES
        }
        
        context.update({
            "is_employee": True,
            "is_employee_list" : True,
            "active_employees_count": active_employees.count(),
            "total_employee_count": total_employees.count(),
            "total_salary": total_salary,
            "active_employees_total_salary": active_employees_total_salary,
            "average_salary": total_salary / len(queryset) if len(queryset) > 0 else 0,
            "active_percentage": (active_employees.count() / len(queryset)) * 100 if len(queryset) > 0 else 0,
            "employment_type_choices": choices.EMPLOYMENT_TYPE_CHOICES,
            "employment_type_counts": employment_type_counts,
            "employment_type_salary": employment_type_salary
        })
        return context
    

class NonActiveEmployeeListView(mixins.HybridListView):
    model = Employee
    table_class = tables.NonActiveEmployeeTable
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")
    filterset_fields = {
        'branch': ['exact'],
        'department': ['exact'],
        'designation': ['exact'],
        'gender': ['exact'],
        'employment_type': ['exact'],
        'status': ['exact']
    }
    search_fields = (
        "user__email",
        "employee_id",
        "first_name",
        "last_name",
        "marital_status",
        "mobile",
        "whatsapp"
    )
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user 
        
        if user.is_superuser:
            pass
        elif hasattr(user, "usertype") and user.usertype == "branch_staff":
            employee = Employee.objects.filter(user=user).first()
            if employee and employee.branch:
                queryset = queryset.filter(branch=employee.branch)

        return queryset.exclude(status="Appointed")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee"] = True
        context["is_non_active_employee_list"] = True
        return context

    
class TeleCallerListView(mixins.HybridListView):
    model = Employee
    table_class = tables.EmployeeTable
    permissions = ("branch_staff", "admin_staff", "sales_head", "ceo","cfo","coo","hr","cmo")
    filterset_fields = {'branch': ['exact'] ,'department': ['exact'], 'designation': ['exact'], 'gender': ['exact'],}
    search_fields = ("user__email", "employee_id", "first_name", "last_name", "marital_status", "mobile", "whatsapp")
    branch_filter = False
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = Employee.objects.filter(user__usertype="tele_caller", is_active=True)

        return queryset
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = Employee.objects.filter(
            Q(user__usertype="tele_caller") | Q(is_also_tele_caller="Yes"),
            is_active=True
        )
        return queryset
    


class EmployeeDetailView(mixins.HybridDetailView):
    queryset = Employee.objects.filter(is_active=True)
    template_name = "employees/employee_detail.html"
    permissions = ("branch_staff", "partner", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "teacher",)


class EmployeeCreateView(mixins.HybridCreateView):
    model = Employee
    form_class = forms.EmployeePersonalDataForm
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")
    template_name = "employees/employee_form.html"
    exclude = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_hrm"] = True
        context["is_personal"] = True
        context["is_create"] = True
        context["subtitle"] = "Personal Data"
        return context

    def get_success_url(self):
        if "save_and_next" in self.request.POST:
            url = build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'})
            return url
        return build_url("employees:employee_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        user = form.save(commit=False)

        if form.cleaned_data.get("password"):
            user.set_password(form.cleaned_data["password"])

        branch = None
        if self.request.user.is_authenticated and hasattr(self.request.user, "branch") and self.request.user.branch:
            branch = self.request.user.branch
        else:
            branch = Branch.objects.first()

        if not branch:
            form.add_error(None, "No branch assigned and no default branch available.")
            return self.form_invalid(form)

        user.branch = branch

        pk = self.kwargs.get("pk")
        if pk:
            employee = get_object_or_404(Employee, pk=pk)
            user.first_name = employee.first_name
            user.last_name = employee.last_name or ""
            user.save()

            employee.user = user
            employee.branch = user.branch
            employee.usertype = user.usertype
            employee.photo = user.image
            employee.save()
        else:
            user.save()

        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return "Employee Personal Data Created Successfully"


class EmployeeUpdateView(mixins.HybridUpdateView):
    model = Employee
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")
    template_name = "employees/employee_form.html"

    def get_initial(self):
        initial = super().get_initial()
        info_type = self.request.GET.get("type", "personal")
        if info_type == "official" and not self.object.employee_id:
            initial['employee_id'] = generate_employee_id()
        return initial

    def get_form_class(self):
        form_classes = {
            "parent": forms.EmployeeParentDataForm,
            "address": forms.EmployeeAddressDataForm,
            "official": forms.EmployeeOfficialDataForm,
            "financial": forms.EmployeeFinancialDataForm,
            "personal": forms.EmployeePersonalDataForm,
        }
        info_type = self.request.GET.get("type", "personal")
        return form_classes.get(info_type, forms.EmployeePersonalDataForm)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        
        try:
            if (hasattr(form, 'cleaned_data') and 
                'branch' in form.cleaned_data and 
                self.object.user is not None):
                
                branch = form.cleaned_data['branch']
                self.object.branch = branch
                self.object.user.branch = branch
                self.object.user.save()
                
        except Exception as e:
            # Log the error or handle it appropriately
            print(f"Error updating branch: {e}")
            # You might want to add a form error here
        
        self.object.save()
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        info_type = self.request.GET.get("type", "personal")
        subtitles = {
            "parent": "Parent Data",
            "address": "Address Data",
            "official": "Official Data",
            "financial": "Financial Data",
            "personal": "Personal Data"
        }
        urls = {
            "personal": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'personal'}),
            "parent": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'}),
            "address": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'address'}),
            "official": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'official'}),
            "financial": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'financial'}),
        }
        context.update({
            "title": "Edit Employee",
            "subtitle": subtitles.get(info_type, "Personal Data"),
            "info_type_urls": urls,
            f"is_{info_type}": True,
            "is_update": True,
            "is_hrm": True,
            "department_form": forms.DepartmentForm(),
            "designation_form": forms.DesignationForm(),
            "course_form": forms.CourseForm(),
        })
        return context

    def get_success_url(self):
        if "save_and_next" in self.request.POST:
            info_type = self.request.GET.get("type", "personal")
            if info_type == "financial" and self.object.user:
                return build_url("accounts:user_update", kwargs={"pk": self.object.user.pk})
            urls = {
                "personal": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'}),
                "parent": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'address'}),
                "address": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'official'}),
                "official": build_url("employees:employee_update", kwargs={"pk": self.object.pk}, query_params={'type': 'financial'}),
                "financial": build_url("accounts:user_create", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'}),
            }
            return urls.get(info_type, self.object.get_list_url())
        return self.object.get_list_url()

    def get_success_message(self, cleaned_data):
        info_type = self.request.GET.get("type", "personal")
        messages_dict = {
            "personal": "Personal data updated successfully.",
            "parent": "Parent data updated successfully.",
            "address": "Address data updated successfully.",
            "official": "Official data updated successfully.",
            "financial": "Financial data updated successfully.",
        }
        return messages_dict.get(info_type, "Data updated successfully.")


class EmployeeDeleteView(mixins.HybridDeleteView):
    model = Employee
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")


class PayrollListView(mixins.HybridListView):
    model = Payroll
    filterset_fields = ("payroll_year", "payroll_month", "employee")
    table_class = tables.PayrollTable
    search_fields = ("employee__fullname", "employee__group", "employee__phone", "employee__staff_id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee"] = True
        context["is_payroll"] = True
        return context


class PayrollCreateView(mixins.HybridCreateView):
    model = Payroll
    form_class = forms.PayrollForm
    template_name = "employees/payroll/payroll_form.html"
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")
    exclude = None


class PayrollDetailView(mixins.HybridDetailView):
    model = Payroll


class PayrollUpdateView(mixins.HybridUpdateView):
    model = Payroll
    form_class = forms.PayrollForm
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")
    exclude = None


class PayrollDeleteView(mixins.HybridDeleteView):
    model = Payroll
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")


class PayrollPaymentListView(mixins.HybridListView):
    model = PayrollPayment
    filterset_fields = ("employee",)
    table_class = tables.PayrollPaymentTable

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee"] = True
        context["is_payroll_payment"] = True
        return context


class PayrollPaymentCreateView(mixins.HybridCreateView):
    model = PayrollPayment
    template_name = "employees/payroll/payroll_payment_form.html"
    form_class = forms.PayrollPaymentForm
    permissions = ("admin_staff", "ceo","cfo","coo","hr","cmo")
    exclude = ("is_active",)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Show all active employees
        form.fields["employee"].queryset = Employee.objects.filter(is_active=True)

        # Payroll queryset → all payrolls of selected employee (only active ones)
        employee_id = self.request.POST.get("employee") or self.request.GET.get("employee")
        payroll_qs = Payroll.objects.none()
        if employee_id:
            payroll_qs = Payroll.objects.filter(
                is_active=True,
                employee_id=employee_id
            )

        if self.request.method == "POST":
            posted_payroll_id = self.request.POST.get("payroll")
            if posted_payroll_id:
                try:
                    posted_payroll = Payroll.objects.get(id=posted_payroll_id)
                    payroll_qs = payroll_qs | Payroll.objects.filter(id=posted_payroll.id)
                except Payroll.DoesNotExist:
                    pass

        form.fields["payroll"].queryset = payroll_qs.distinct()
        return form

    def form_valid(self, form):
        form.instance.is_active = True

        payroll = form.cleaned_data['payroll']
        amount_paid_now = form.cleaned_data['amount_paid']

        with transaction.atomic():  # ensure atomic operation
            # Save the new payment
            response = super().form_valid(form)

            # Calculate total paid including this payment
            total_paid = PayrollPayment.objects.filter(
                payroll=payroll, is_active=True
            ).aggregate(total=Sum("amount_paid"))["total"] or 0

            remaining_due = payroll.net_salary - total_paid

            if remaining_due <= 0:
                payroll.status = "Completed"
                payroll.save()

        return response

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)


class PayrollPaymentDetailView(mixins.HybridDetailView):
    model = PayrollPayment


class PayrollPaymentUpdateView(mixins.HybridUpdateView):
    model = PayrollPayment
    form_class = forms.PayrollPaymentForm
    permissions = ("admin_staff", "ceo", "cfo", "coo", "hr", "cmo")
    template_name = "employees/payroll/payroll_payment_form.html"

    def form_valid(self, form):
        payroll = form.cleaned_data['payroll']
        amount_paid_now = form.cleaned_data['amount_paid']

        with transaction.atomic():
            # Save the updated payment
            response = super().form_valid(form)

            # Recalculate total paid (exclude this instance, then add new value)
            total_paid = PayrollPayment.objects.filter(
                payroll=payroll, is_active=True
            ).exclude(id=self.object.id).aggregate(total=Sum("amount_paid"))["total"] or 0

            total_paid += amount_paid_now

            remaining_due = payroll.net_salary - total_paid

            # Update payroll status correctly
            if remaining_due <= 0:
                payroll.status = "Completed"
            else:
                payroll.status = "Pending"
            payroll.save(update_fields=["status"])

        return response

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)


class PayrollPaymentDeleteView(mixins.HybridDeleteView):
    model = PayrollPayment



class AdvancePayrollPaymentListView(mixins.HybridListView):
    model = AdvancePayrollPayment
    filterset_fields = ("employee",)
    table_class = tables.AdvancePayrollPaymentTable

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee"] = True
        context["is_advance_payroll_payment"] = True
        return context


class AdvancePayrollPaymentCreateView(mixins.HybridCreateView):
    model = AdvancePayrollPayment
    template_name = "employees/payroll/advance_payroll_payment_form.html"
    form_class = forms.AdvancePayrollPaymentForm
    permissions = ("admin_staff", "ceo", "cfo", "coo", "hr", "cmo")
    exclude = ("is_active",)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Employee queryset
        active_employees = Employee.objects.filter(is_active=True, status="Appointed")

        inactive_employees_with_due = []
        for employee in Employee.objects.all():
            total_due_amount = Payroll.objects.filter(
                is_active=True, employee=employee
            ).aggregate(total=Sum("net_salary"))["total"] or 0

            total_paid_amount = AdvancePayrollPayment.objects.filter(
                is_active=True, employee=employee
            ).aggregate(total=Sum("amount_paid"))["total"] or 0

            pending_due = total_due_amount - total_paid_amount
            if pending_due > 0:
                inactive_employees_with_due.append(employee.id)

        inactive_employees = Employee.objects.filter(id__in=inactive_employees_with_due)
        form.fields["employee"].queryset = (active_employees | inactive_employees).distinct()

        # Payroll queryset
        employee_id = self.request.POST.get("employee") or self.request.GET.get("employee")
        payroll_qs = Payroll.objects.none()
        if employee_id:
            payroll_qs = Payroll.objects.filter(is_active=True, employee_id=employee_id)

        if self.request.method == "POST":
            posted_payroll_id = self.request.POST.get("payroll")
            if posted_payroll_id:
                try:
                    posted_payroll = Payroll.objects.get(id=posted_payroll_id)
                    payroll_qs = payroll_qs | Payroll.objects.filter(id=posted_payroll.id)
                except Payroll.DoesNotExist:
                    pass

        form.fields["payroll"].queryset = payroll_qs.distinct()
        return form

    def form_valid(self, form):
        form.instance.is_active = True
        payroll = form.cleaned_data["payroll"]
        amount_paid_now = form.cleaned_data["amount_paid"]

        with transaction.atomic():
            # Calculate total already paid in advances
            total_advance_paid = AdvancePayrollPayment.objects.filter(
                payroll=payroll, is_active=True
            ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")

            # Max allowed = 75% of basic salary
            max_allowed = payroll.basic_salary * Decimal("0.75")

            if total_advance_paid + amount_paid_now > max_allowed:
                form.add_error(
                    "amount_paid",
                    f"Total advances cannot exceed 75% of basic salary ({max_allowed}). "
                    f"Already paid: {total_advance_paid}, trying to add: {amount_paid_now}"
                )
                return self.form_invalid(form)

            # Save the new payment
            response = super().form_valid(form)

        return response

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)


class AdvancePayrollPaymentDetailView(mixins.HybridDetailView):
    model = AdvancePayrollPayment


class AdvancePayrollPaymentUpdateView(mixins.HybridUpdateView):
    model = AdvancePayrollPayment
    form_class = forms.AdvancePayrollPaymentForm
    permissions = ("admin_staff", "ceo", "cfo", "coo", "hr", "cmo")
    template_name = "employees/payroll/advance_payroll_payment_form.html"

    def form_valid(self, form):
        payroll = form.cleaned_data['payroll']

        with transaction.atomic():
            # Save the updated payment
            response = super().form_valid(form)

            # Total from Advance payments
            advance_paid = AdvancePayrollPayment.objects.filter(
                payroll=payroll, is_active=True
            ).aggregate(total=Sum("amount_paid"))["total"] or 0

            # Total from Normal payroll payments
            regular_paid = PayrollPayment.objects.filter(
                payroll=payroll, is_active=True
            ).aggregate(total=Sum("amount_paid"))["total"] or 0

            total_paid = advance_paid + regular_paid
            remaining_due = payroll.net_salary - total_paid

            # Update payroll status
            if remaining_due <= 0:
                payroll.status = "Completed"
            else:
                payroll.status = "Pending"
            payroll.save()

        return response

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)


class AdvancePayrollPaymentDeleteView(mixins.HybridDeleteView):
    model = AdvancePayrollPayment


class PayrollReportView(mixins.HybridListView):
    title = "Payroll Report"
    template_name = "employees/payroll/payroll_report.html"
    table_class = tables.PayrollReportTable
    model = Employee
    filterset_fields ={
        "branch": ["exact"],
        "employee_id": ["icontains"],
        "department": ["exact"],
        "designation": ["exact"],
        "employment_type": ["exact"],
        "status": ["exact"],
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee"] = True
        context["is_payroll_report"] = True
        context["hide_zero"] = self.request.GET.get("hide_zero", False)
        context["can_add"] = False
        context["title"] = "Payroll Report"
        return context

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, status="Appointed")

    def get_table(self, **kwargs):
        hide_zero = self.request.GET.get("hide_zero", "false")
        data = []
        for employee in self.get_queryset():
            total_due_amount = Payroll.objects.filter(is_active=True, employee=employee).aggregate(Sum("net_salary"))["net_salary__sum"]
            total_paid_amount = PayrollPayment.objects.filter(is_active=True, employee=employee).aggregate(Sum("amount_paid"))["amount_paid__sum"]
            total_advance_amount = AdvancePayrollPayment.objects.filter(is_active=True, employee=employee).aggregate(Sum("amount_paid"))["amount_paid__sum"]

            total_due = total_due_amount if total_due_amount else 0
            total_paid = total_paid_amount if total_paid_amount else 0
            pending_due = (total_due - total_paid) if total_due > total_paid else 0
            advance_paid = total_advance_amount if total_advance_amount else 0

            if hide_zero == "true" and (total_due - total_paid) == 0:
                continue

            data.append(
                {
                    "employee": employee.fullname,
                    "total_due": mark_safe(f"<span>{float(total_due)}</span>"),
                    "total_paid": mark_safe(f"<span class='text-success'>{float(total_paid)}</span>"),
                    "pending_due": mark_safe(f"<span class='text-danger'>{float(pending_due)}</span>"),
                    "advance_paid": mark_safe(f"<span class='text-info'>{float(advance_paid)}</span>"),
                    "view_details": mark_safe(
                        f"<a href='{reverse('employees:payroll_report_detail', kwargs={'pk': employee.pk})}' class='btn btn-sm btn-light btn-outline-info'>View Details</a>"
                    ),
                    "view_slip": mark_safe(
                        f"<a href='{reverse('employees:payroll_report_slip', kwargs={'pk': employee.pk})}' class='btn btn-sm btn-light btn-outline-info'>View Slip</a>"
                    ),
                }
            )

        sorted_data = sorted(data, key=lambda x: x["pending_due"], reverse=True)
        return self.table_class(sorted_data, request=self.request)
    

class InactivePayrollReportView(mixins.HybridListView):
    title = "Payroll Report"
    # template_name = "app/custom/payroll_report.html"
    table_class = tables.PayrollReportTable
    model = Employee
    filterset_fields ={
        "branch": ["exact"],
        "department": ["exact"],
        "designation": ["exact"],
        "employment_type": ["exact"],
        "status": ["exact"],
        "employee_id": ["icontains"],
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hide_zero"] = self.request.GET.get("hide_zero", False)
        return context

    def get_queryset(self):
        return super().get_queryset().exclude(status="Appointed")

    def get_table(self, **kwargs):
        hide_zero = self.request.GET.get("hide_zero", "false")
        data = []
        for employee in self.get_queryset():
            total_due_amount = Payroll.objects.filter(is_active=True, employee=employee).aggregate(Sum("net_salary"))["net_salary__sum"]
            total_paid_amount = PayrollPayment.objects.filter(is_active=True, employee=employee).aggregate(Sum("amount_paid"))["amount_paid__sum"]
            total_advance_amount = AdvancePayrollPayment.objects.filter(is_active=True, employee=employee).aggregate(Sum("amount_paid"))["amount_paid__sum"]

            total_due = total_due_amount if total_due_amount else 0
            total_paid = total_paid_amount if total_paid_amount else 0
            pending_due = (total_due - total_paid) if total_due > total_paid else 0
            advance_paid = total_advance_amount if total_advance_amount else 0
            if hide_zero == "true" and (total_due - total_paid) == 0:
                continue
            data.append(
                {
                    "employee": employee.fullname(),
                    "total_due": mark_safe(f"<span>{float(total_due)}</span>"),
                    "total_paid": mark_safe(f"<span class='text-success'>{float(total_paid)}</span>"),
                    "pending_due": mark_safe(f"<span class='text-danger'>{float(pending_due)}</span>"),
                    "advance_paid": mark_safe(f"<span class='text-info'>{float(advance_paid)}</span>"),
                    "view_details": mark_safe(
                        f"<a href='{reverse('payroll:payroll_report_detail', kwargs={'pk': staff.pk})}' class='btn btn-sm btn-light btn-outline-info'>View Details</a>"
                    ),
                    "view_slip": mark_safe(
                        f"<a href='{reverse('payroll:payroll_report_slip', kwargs={'pk': staff.pk})}' class='btn btn-sm btn-light btn-outline-info'>View Slip</a>"
                    ),
                }
            )
        sorted_data = sorted(data, key=lambda x: x["pending_due"], reverse=True)
        return self.table_class(sorted_data)


class PayrollReportDetailView(mixins.HybridTemplateView):
    template_name = "employees/payroll/payroll_report_detail.html"
    title = "Payroll Report Detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = Employee.objects.get(pk=self.kwargs["pk"])

        # Filters
        year_filter = self.request.GET.get('year')
        month_filter = self.request.GET.get('month')
        status_filter = self.request.GET.get('status')

        # Base payroll queryset
        payrolls = Payroll.objects.filter(is_active=True, employee=employee)

        # Apply filters
        if year_filter and year_filter != "all":
            payrolls = payrolls.filter(payroll_year=year_filter)
        if month_filter and month_filter != "all":
            payrolls = payrolls.filter(payroll_month=month_filter)
        if status_filter and status_filter != "all":
            payrolls = payrolls.filter(status=status_filter)

        # Payroll payments
        payroll_payments = PayrollPayment.objects.filter(
            is_active=True,
            payroll__in=payrolls
        ).order_by('-payment_date')

        # Advance payments
        advance_payments = AdvancePayrollPayment.objects.filter(
            is_active=True,
            employee=employee,
            payroll__in=payrolls
        ).order_by('-payment_date')

        # Totals
        total_due_amount = payrolls.aggregate(Sum("net_salary"))["net_salary__sum"] or 0
        total_paid_amount = payroll_payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        total_advance_paid = advance_payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0

        total_paid_with_advance = total_paid_amount + total_advance_paid
        pending_due = max(total_due_amount - total_paid_with_advance, 0)

        # Dropdowns
        all_payrolls = Payroll.objects.filter(employee=employee, is_active=True)
        years = all_payrolls.values_list('payroll_year', flat=True).distinct().order_by('payroll_year')
        months = all_payrolls.values_list('payroll_month', flat=True).distinct().order_by('payroll_month')
        month_choices = [(m, calendar.month_name[int(m)]) for m in months if m.isdigit()]

        context.update({
            "employee": employee,
            "payrolls": payrolls,
            "payments": payroll_payments,
            "advance_payments": advance_payments,
            "years": years,
            "month_choices": month_choices,
            "status_choices": choices.PAYROLL_STATUS,
            "total_due": float(total_due_amount),
            "total_paid": float(total_paid_amount),
            "advance_paid": float(total_advance_paid),  # new
            "pending_due": float(pending_due),
            "title": f"Payroll Report Detail - {employee.fullname()}",
            "current_filters": {
                'year': year_filter or 'all',
                'month': month_filter or 'all',
                'status': status_filter or 'all'
            },
            "can_add_users": (
                self.request.user.is_superuser
                or getattr(self.request.user, "usertype", "") in ["admin_staff", "ceo", "cfo"]
            ),
        })
        return context


class PayrollReportSlipView(mixins.HybridTemplateView):
    template_name = "employees/payroll/payroll_report_slip.html"
    title = "Payroll Report Slip"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = get_object_or_404(Employee, pk=self.kwargs["pk"])

        selected_payroll_id = self.request.GET.get("payroll")

        payroll_qs = Payroll.objects.filter(
            is_active=True,
            employee=employee
        ).order_by("-payroll_year", "-payroll_month")

        month_name = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        payroll_list = [
            {
                "id": p.id,
                "month": int(p.payroll_month),
                "year": int(p.payroll_year),
                "label": f"{month_name[int(p.payroll_month)]} - {p.payroll_year}"
            }
            for p in payroll_qs
        ]

        if selected_payroll_id:
            try:
                latest_payroll = Payroll.objects.get(id=selected_payroll_id, is_active=True)
            except Payroll.DoesNotExist:
                latest_payroll = payroll_qs.first()
        else:
            latest_payroll = payroll_qs.first()

        if latest_payroll:
            payroll_payments = PayrollPayment.objects.filter(
                is_active=True,
                employee=employee,
                payment_date__year=latest_payroll.payroll_year,
                payment_date__month=latest_payroll.payroll_month
            )
            advance_payments = AdvancePayrollPayment.objects.filter(
                is_active=True,
                employee=employee,
                payroll=latest_payroll
            )
        else:
            payroll_payments = PayrollPayment.objects.none()
            advance_payments = AdvancePayrollPayment.objects.none()

        total_paid = payroll_payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        total_advance = advance_payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        total_paid_all = total_paid + total_advance

        selected_month_net_salary = latest_payroll.net_salary if latest_payroll else 0
        month_balance = max(selected_month_net_salary - total_paid_all, 0)

        total_due = payroll_qs.aggregate(Sum("net_salary"))["net_salary__sum"] or 0
        pending_due = max(total_due - total_paid_all, 0)

        paid_leave = full_day_leave = half_day_leave = total_leave = 0.0
        if latest_payroll:
            absences = float(latest_payroll.absences or 0)
            total_leave = absences
            if employee.employment_type == "PROBATION":
                full_day_leave = absences
            else:
                if absences <= 1:
                    paid_leave = absences
                else:
                    paid_leave = 1
                    remaining = absences - 1
                    full_day_leave = int(remaining)
                    if remaining - full_day_leave >= 0.5:
                        half_day_leave = 1

        context.update({
            "employee": employee,
            "latest_payroll": latest_payroll,
            "payroll_list": payroll_list,
            "payment_lists": payroll_payments,
            "advance_payment_lists": advance_payments,
            "total_due": float(total_due),
            "total_paid": float(total_paid),
            "total_advance": float(total_advance),
            "total_paid_all": float(total_paid_all),
            "pending_due": float(pending_due),
            "month_balance": float(month_balance),
            "current_date": now().date(),
            "paid_leave": paid_leave,
            "full_day_leave": full_day_leave,
            "half_day_leave": half_day_leave,
            "total_leave": total_leave,
        })
        return context

    
class PartnerListView(mixins.HybridListView):
    model = Partner
    table_class = tables.PartnerTable
    filterset_fields ={'partner_id': ['icontains'], }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_partner"] = True
        return context
    

class PartnerDetailView(mixins.HybridDetailView):
    model = Partner
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "teacher",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_partner"] = True
        return context
    

class PartnerCreateView(mixins.HybridCreateView):
    model = Partner
    form_class = forms.PartnerForm
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo",)
    template_name = "employees/partner/partner_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "is_partner": True,
            "is_create": True,
            "title": "Create Partner",
            "subtitle": "Partner Information",
        })
        return context

    def form_valid(self, form):
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")

        User = get_user_model()

        user = User.objects.create(
            email=email,
            first_name=form.cleaned_data.get("full_name").split(" ")[0],
            last_name=" ".join(form.cleaned_data.get("full_name").split(" ")[1:]),
            usertype="partner",
            password=make_password(password),
            is_active=True,
        )

        partner = form.save(commit=False)
        partner.user = user

        if not partner.partner_id:
            partner.partner_id = f"P{Partner.objects.count() + 1:05d}"

        partner.save()

        self.object = partner
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return "Partner and account created successfully."

    def get_success_url(self):
        return self.object.get_list_url()


class PartnerUpdateView(mixins.HybridUpdateView):
    model = Partner
    form_class = forms.PartnerForm
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo",)
    template_name = "employees/partner/partner_form.html"

    def get_form_class(self):
        """
        Use the same PartnerForm but hide password fields during update.
        """
        form_class = super().get_form_class()

        # Create a subclass of the form dynamically to make password fields optional or hidden
        class UpdatePartnerForm(form_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Remove password fields for update
                self.fields.pop("password", None)
                self.fields.pop("confirm_password", None)

        return UpdatePartnerForm

    def get_initial(self):
        """
        Pre-fill initial data from the related User.
        """
        partner = self.get_object()
        initial = super().get_initial()
        if partner.user:
            initial.update({
                "email": partner.user.email,
                "full_name": f"{partner.user.first_name} {partner.user.last_name}".strip(),
            })
        return initial

    def form_valid(self, form):
        """
        Save changes to both Partner and User.
        """
        partner = form.save(commit=False)
        user = partner.user

        # Update linked User details
        full_name = form.cleaned_data.get("full_name", "")
        first_name, *last_name = full_name.split(" ", 1)
        user.first_name = first_name
        user.last_name = last_name[0] if last_name else ""
        user.email = form.cleaned_data.get("email")
        user.username = form.cleaned_data.get("email")
        user.save()

        partner.save()
        self.object = partner
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "is_partner": True,
            "is_update": True,
            "title": "Update Partner",
            "subtitle": "Modify Partner Information",
        })
        return context

    def get_success_message(self, cleaned_data):
        return "Partner information updated successfully."

    def get_success_url(self):
        return self.object.get_list_url()

    
class PartnerDeleteView(mixins.HybridDeleteView):
    model = Partner
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo",)


class EmployeeLeaveRequestListView(mixins.HybridListView):
    model = EmployeeLeaveRequest
    table_class = tables.EmployeeLeaveRequestTable
    template_name = "employees/employee_leave_request/employee_leaverequest_list.html"
    filterset_fields = {
        "employee__branch": ["exact"],
        "employee": ["exact"],
        "status": ["exact"],
    }
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "teacher", "mentor", "sales_head", "tele_caller")

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        management_roles = ["admin_staff", "hr", "ceo", "cfo", "coo", "branch_staff"]
        
        if user.is_superuser or user.groups.filter(name__in=management_roles).exists():
            return queryset
            
        if hasattr(user, 'employee') and user.employee:
            return queryset.filter(employee=user.employee)
            
        return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        qs = self.get_queryset()

        context["status_counts"] = {
            "approved": qs.filter(status="approved").count(),
            "rejected": qs.filter(status="rejected").count(),
            "pending": qs.filter(status="pending").count(),
            "all": qs.count(),
        }
        
        context["is_employee_leave_request"] = True
        context["can_add"] = True
        context["new_link"] = reverse_lazy("employees:employee_leave_request_create")
        return context
    

class EmployeeLeaveRequestDetailView(mixins.HybridDetailView):
    model = EmployeeLeaveRequest
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "teacher", "mentor", "sales_head", "tele_caller")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee_leave_request"] = True
        return context

    
class EmployeeLeaveRequestCreateView(mixins.HybridCreateView):
    model = EmployeeLeaveRequest
    form_class = forms.EmployeeLeaveRequestForm
    template_name = "employees/employee_leave_request/employee_leaverequest_form.html"
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "teacher", "mentor", "sales_head", "tele_caller")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee_leave_request"] = True
        context["is_create"] = True
        return context

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'employee') or request.user.employee is None:
            messages.error(request, "You must be an employee to create a leave request.")
            return redirect("employees:employee_leave_request_list")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.employee = self.request.user.employee
        return form

    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        return super().form_valid(form)

    
class EmployeeLeaveRequestUpdateView(mixins.HybridUpdateView):
    model = EmployeeLeaveRequest
    form_class = forms.EmployeeLeaveRequestForm
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "teacher", "mentor", "sales_head", "tele_caller")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_employee_leave_request"] = True
        context["is_update"] = True
        return context
    

class EmployeeLeaveRequestDeleteView(mixins.HybridDeleteView):
    model = EmployeeLeaveRequest
    permissions = ("branch_staff", "admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "teacher", "mentor", "sales_head", "tele_caller")


class EmployeeLeaveReport(mixins.HybridListView):
    model = Employee
    table_class = tables.EmployeeLeaveReportTable 
    filterset_fields = {
        "branch": ['exact'], 
        "department": ['exact'], 
        "designation": ['exact']
    }
    permissions = ("admin_staff", "ceo", "cfo", "coo", "hr", "cmo",)

    def get_queryset(self):
        return super().get_queryset().select_related(
            'leave_balance', 'department', 'designation', 'branch'
        ).prefetch_related('leave_requests')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Employee Leave Report"
        context["is_employee_leave_report"] = True
        return context


class EmployeeLeaveReportDetailView(mixins.HybridDetailView):
    model = Employee
    permissions = ("admin_staff", "ceo", "cfo", "coo", "hr", "cmo",)
    template_name = "employees/employee_leave_request/report/report_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        
        leave_history = employee.leave_requests.filter(is_active=True).order_by('-start_date')

        leave_type = self.request.GET.get('leave_type')
        status = self.request.GET.get('status')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if leave_type:
            leave_history = leave_history.filter(leave_type=leave_type)
        if status:
            leave_history = leave_history.filter(status=status)
        if start_date:
            leave_history = leave_history.filter(start_date__gte=start_date)
        if end_date:
            leave_history = leave_history.filter(end_date__lte=end_date)

        context["leave_history"] = leave_history
        context["leave_types"] = EmployeeLeaveRequest.LEAVE_TYPE_CHOICES
        context["status_choices"] = EmployeeLeaveRequest.LEAVE_STATUS_CHOICES
        return context