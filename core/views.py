import os
import qrcode
import base64
from io import BytesIO
from core import mixins
from decimal import Decimal
from django.utils.timezone import now
from django.db.models import Q
from django_tables2 import RequestConfig
from django.db.models import Count
from core.pdfview import PDFView
from datetime import date, datetime, timedelta
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.conf import settings
from django.template import loader
from django.test import override_settings
from collections import defaultdict
from branches.models import Branch
from core.models import Setting
from branches.tables import BranchTable
from admission.models import Admission, Attendance, FeeReceipt, AdmissionEnquiry, FeeStructure
from admission.tables import AdmissionEnquiryTable
from employees.models import Employee, Partner
from masters.models import Batch, Course, HeroBanner, Holiday, LeaveRequest, RequestSubmission

from .forms import HomeForm
from .models import CompanyProfile
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy

from django.views import View
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.staticfiles import finders

from core.tables import SettingsTable


class HomeView(mixins.HybridTemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["is_home"] = True

        # Define the stages to include in financial calculations
        FINANCIAL_STAGES = ["active", "completed", "placed", "internship"]

        assigned_requests = RequestSubmission.objects.filter(is_active=True)

        if user.usertype == "branch_staff":
            context["assigned_requests"] = assigned_requests.filter(current_usertype=user.usertype, creator=user).order_by('-created')
        else:
            context["assigned_requests"] = assigned_requests.filter(current_usertype=user.usertype).order_by('-created')

        # --- UPDATED: Main Dashboard Totals Calculation ---
        # Removed is_active=True and filtered by specific stage_statuses
        students = Admission.objects.filter(
            stage_status__in=FINANCIAL_STAGES
        )
        
        # We keep is_active=True for receipts/structures to avoid calculating deleted/voided records,
        # but they are now linked to the broader range of students defined above.
        fee_receipts = FeeReceipt.objects.filter(
            is_active=True,
            student__in=students
        )
        fee_structures = FeeStructure.objects.filter(
            student__in=students,
            is_active=True,
        )

        total_paid_amount = fee_receipts.aggregate(
            total=Sum('payment_methods__amount')
        )['total'] or Decimal('0.00')

        total_fee = fee_structures.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        total_due_amount = max(total_fee - total_paid_amount, Decimal('0.00'))

        context["due_amount"] = total_due_amount
        context["total_paid"] = total_paid_amount
        context["total_amount"] = total_fee

        months = [
            "January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"
        ]

        if user.usertype == "student":
            context["hero_banners"] = HeroBanner.objects.filter(
                is_active=True, banner_type__in=["student", "all"]
            ).order_by("-created")

            try:
                admission = Admission.objects.get(user=user)
                student_admission = Admission.objects.get(user=user)
                
                subscription_overview = admission.get_subscription_overview()
                current_month_subscription = admission.get_current_month_subscription()
                
                show_subscription_popup = False
                if current_month_subscription:
                    show_subscription_popup = True
                
                context["show_subscription_popup"] = show_subscription_popup
                context["current_month_subscription"] = current_month_subscription
                context["subscription_overview"] = subscription_overview
                context["all_fee_structures"] = FeeStructure.objects.filter(
                    student=admission
                ).order_by('installment_no')
                
                attendance_records = Attendance.objects.filter(student=student_admission, is_active=True)

                leave_requests = LeaveRequest.objects.filter(student=student_admission)

                leave_map = {}
                for leave in leave_requests:
                    current = leave.start_date
                    while current <= leave.end_date:
                        leave_map[current] = {
                            "status": leave.status.lower(),
                            "subject": leave.subject,
                            "reason": leave.reason,
                            "attachment": leave.attachment.url if leave.attachment else None,
                        }
                        current += timedelta(days=1)

                start_year = admission.batch.starting_date.year
                
                batch_end_date = getattr(admission.batch, "ending_date", None)
                if batch_end_date:
                    end_year = batch_end_date.year
                else:
                    end_year = date.today().year

                months = []
                for year in range(start_year, end_year + 1):
                    for month in range(1, 13):
                        months.append((date(year, month, 1).strftime("%B"), year))

                attendance_by_month = {}
                for month_name, year_num in months:
                    unique_key = f"{month_name}-{year_num}"
                    attendance_by_month[unique_key] = {
                        "month": month_name, 
                        "year": year_num,
                        "records": [], 
                        "total_present": 0, 
                        "total_absent": 0, 
                        "total_holiday": 0
                    }

                total_present, total_absent, total_holiday = 0, 0, 0

                for month_name, year_num in months:
                    unique_key = f"{month_name}-{year_num}"
                    
                    month_num = None
                    for test_month in range(1, 13):
                        if date(2000, test_month, 1).strftime("%B") == month_name:
                            month_num = test_month
                            break
                    
                    holidays = Holiday.objects.filter(
                        is_active=True,
                        date__month=month_num,
                        date__year=year_num
                    ).filter(
                        Q(scope="all") | Q(branch=admission.branch)
                    )

                    holiday_map = {}
                    for holiday in holidays:
                        if holiday.scope == "branch" and not holiday.branch.filter(id=admission.branch.id).exists():
                            continue
                        holiday_map[holiday.date.day] = {
                            "name": holiday.name,
                            "is_auto": holiday.is_auto_holiday,
                        }

                    import calendar
                    days_in_month = calendar.monthrange(year_num, month_num)[1]
                    for day in range(1, days_in_month + 1):
                        current_date_obj = date(year_num, month_num, day)
                        is_auto_holiday, holiday_name = Holiday.is_auto_holiday(current_date_obj)
                        if is_auto_holiday and day not in holiday_map:
                            holiday_map[day] = {"name": holiday_name, "is_auto": True}

                    month_records = [
                        record
                        for record in attendance_records
                        if record.register.date.month == month_num and record.register.date.year == year_num
                    ]

                    all_records = []
                    for day in range(1, days_in_month + 1):
                        current_date_obj = date(year_num, month_num, day)
                        is_holiday = day in holiday_map
                        holiday_info = holiday_map.get(day)
                        
                        existing_record = next(
                            (r for r in month_records if r.register.date.day == day), None
                        )

                        if existing_record:
                            if is_holiday:
                                existing_record.status = "Holiday"
                                existing_record.is_holiday = True
                                existing_record.holiday_name = holiday_info["name"]
                                existing_record.is_auto_holiday = holiday_info["is_auto"]
                            else:
                                existing_record.is_holiday = False
                            existing_record.has_data = True

                            leave_info = leave_map.get(current_date_obj)
                            if leave_info:
                                existing_record.leave_status = leave_info["status"]
                                existing_record.leave_subject = leave_info["subject"]
                                existing_record.leave_reason = leave_info["reason"]
                                existing_record.leave_attachment = leave_info["attachment"]
                            else:
                                existing_record.leave_status = None
                                existing_record.leave_subject = None
                                existing_record.leave_reason = None
                                existing_record.leave_attachment = None

                            all_records.append(existing_record)

                        else:
                            if is_holiday:
                                placeholder = type("obj", (object,), {
                                    "register": type("obj", (object,), {"date": current_date_obj}),
                                    "status": "Holiday",
                                    "is_holiday": True,
                                    "holiday_name": holiday_info["name"],
                                    "is_auto_holiday": holiday_info["is_auto"],
                                    "leave_status": None, "leave_subject": None,
                                    "leave_reason": None, "leave_attachment": None,
                                    "has_data": True,
                                })()
                            else:
                                leave_info = leave_map.get(current_date_obj)
                                if leave_info:
                                    placeholder = type("obj", (object,), {
                                        "register": type("obj", (object,), {"date": current_date_obj}),
                                        "status": "Absent",
                                        "is_holiday": False, "holiday_name": None, "is_auto_holiday": False,
                                        "leave_status": leave_info["status"],
                                        "leave_subject": leave_info["subject"],
                                        "leave_reason": leave_info["reason"],
                                        "leave_attachment": leave_info["attachment"],
                                        "has_data": True,
                                    })()
                                else:
                                    placeholder = type("obj", (object,), {
                                        "register": type("obj", (object,), {"date": current_date_obj}),
                                        "status": None,
                                        "is_holiday": False, "holiday_name": None, "is_auto_holiday": False,
                                        "leave_status": None, "leave_subject": None,
                                        "leave_reason": None, "leave_attachment": None,
                                        "has_data": False,
                                    })()
                            all_records.append(placeholder)

                    present_count = len([r for r in all_records if getattr(r, "status", None) == "Present"])
                    absent_count = len([r for r in all_records if getattr(r, "status", None) == "Absent"])
                    holiday_count = len([r for r in all_records if getattr(r, "is_holiday", False)])

                    attendance_by_month[unique_key]["records"] = all_records
                    attendance_by_month[unique_key]["total_present"] = present_count
                    attendance_by_month[unique_key]["total_absent"] = absent_count
                    attendance_by_month[unique_key]["total_holiday"] = holiday_count

                    total_present += present_count
                    total_absent += absent_count
                    total_holiday += holiday_count

                context["attendance_by_month"] = attendance_by_month 
                context["attendance_by_month_list"] = list(attendance_by_month.values()) 
                context["days_in_month"] = [f"{day:02d}" for day in range(1, 32)]
                context["total_present"] = total_present
                context["total_absent"] = total_absent
                context["total_holiday"] = total_holiday
                context["admission"] = admission

            except Admission.DoesNotExist:
                context["attendance_by_month"] = {}
                context["attendance_by_month_list"] = []
                context["days_in_month"] = [f"{day:02d}" for day in range(1, 32)]
                context["total_present"] = 0
                context["total_absent"] = 0
                context["total_holiday"] = 0
                context["admission"] = None
                context["show_subscription_popup"] = False

        elif user.usertype == "teacher":
            teacher = Employee.objects.select_related("course", "branch").filter(user=user).first()

            if teacher:
                current_date = now().date()
                selected_month = int(self.request.GET.get('month', current_date.month))
                selected_year = int(self.request.GET.get('year', current_date.year))
                
                selected_batch = self.request.GET.get('batch', 'all-students')
                
                if selected_month < 1 or selected_month > 12:
                    selected_month = current_date.month
                if selected_year < 2020 or selected_year > current_date.year + 1:
                    selected_year = current_date.year

                start_month_date = date(selected_year, selected_month, 1)

                student_list = Admission.objects.select_related(
                    "course", "branch", "user", "batch"
                ).filter(
                    course=teacher.course,
                    branch=teacher.branch,
                    batch__status="in_progress",
                    is_active=True
                ).filter(
                    Q(stage_status="active") |
                    Q(studentstagestatushistory__created__gte=start_month_date)
                ).distinct().order_by("first_name", "last_name")

                students_by_batch_temp = {}
                for student in student_list:
                    batch_name = student.batch.batch_name if student.batch else "No Batch"
                    if batch_name not in students_by_batch_temp:
                        students_by_batch_temp[batch_name] = []
                    students_by_batch_temp[batch_name].append(student)

                if selected_batch and selected_batch != 'all-students':
                    try:
                        batch_id = int(selected_batch)
                        student_list = student_list.filter(batch_id=batch_id)
                        students_by_batch_temp = {}
                        for student in student_list:
                            batch_name = student.batch.batch_name if student.batch else "No Batch"
                            if batch_name not in students_by_batch_temp:
                                students_by_batch_temp[batch_name] = []
                            students_by_batch_temp[batch_name].append(student)
                    except ValueError:
                        pass  

                monthly_attendance = Attendance.objects.select_related("student", "register").filter(
                    student__in=student_list,
                    is_active=True,
                    register__date__month=selected_month,
                    register__date__year=selected_year
                )

                today = now().date()
                today_attendance = Attendance.objects.select_related("student", "register").filter(
                    student__in=student_list,
                    is_active=True,
                    register__date=today
                )

                student_ids = student_list.values_list('id', flat=True)
                leave_requests = LeaveRequest.objects.filter(student_id__in=student_ids)
                
                leave_map = {}
                for leave in leave_requests:
                    current = leave.start_date
                    while current <= leave.end_date:
                        key = (leave.student_id, current)
                        leave_map[key] = {
                            "status": leave.status.lower(),
                            "subject": leave.subject,
                            "reason": leave.reason,
                            "attachment": leave.attachment if leave.attachment else None,
                        }
                        current += timedelta(days=1)

                holidays = Holiday.objects.filter(
                    is_active=True,
                    date__month=selected_month,
                    date__year=selected_year
                ).filter(
                    branch=teacher.branch
                )

                holiday_map = {}
                for holiday in holidays:
                    if holiday.scope == 'branch' and not holiday.branch.filter(id=teacher.branch.id).exists():
                        continue
                    holiday_map[holiday.date.day] = {
                        'name': holiday.name,
                        'is_auto': holiday.is_auto_holiday
                    }

                import calendar
                days_in_month = calendar.monthrange(selected_year, selected_month)[1]
                for day in range(1, days_in_month + 1):
                    current_date_obj = date(selected_year, selected_month, day)
                    is_auto_holiday, holiday_name = Holiday.is_auto_holiday(current_date_obj)
                    if is_auto_holiday and day not in holiday_map:
                        holiday_map[day] = {
                            'name': holiday_name,
                            'is_auto': True
                        }

                students_by_batch = {}
                attendance_by_student = {}
                
                for student in student_list:
                    batch_name = student.batch.batch_name if student.batch else "No Batch"
                    if batch_name not in students_by_batch:
                        students_by_batch[batch_name] = []
                    students_by_batch[batch_name].append(student)

                    records = monthly_attendance.filter(student=student, is_active=True)
                    
                    all_records = []
                    
                    for day in range(1, days_in_month + 1):
                        current_date_obj = date(selected_year, selected_month, day)
                        
                        is_holiday = day in holiday_map
                        holiday_info = holiday_map.get(day)
                        
                        existing_record = None
                        for record in records:
                            if record.register.date == current_date_obj:
                                existing_record = record
                                break
                        
                        if existing_record:
                            if is_holiday:
                                existing_record.status = 'Holiday'
                                existing_record.is_holiday = True
                                existing_record.holiday_name = holiday_info['name']
                                existing_record.is_auto_holiday = holiday_info['is_auto']
                                existing_record.has_data = True
                            else:
                                existing_record.has_data = True
                            
                            leave_info = leave_map.get((student.id, current_date_obj))
                            if leave_info:
                                existing_record.leave_status = leave_info["status"]
                                existing_record.leave_subject = leave_info["subject"]
                                existing_record.leave_reason = leave_info["reason"]
                                existing_record.leave_attachment = leave_info["attachment"]
                            else:
                                existing_record.leave_status = None
                                existing_record.leave_subject = None
                                existing_record.leave_reason = None
                                existing_record.leave_attachment = None
                            
                            all_records.append(existing_record)
                        else:
                            if is_holiday:
                                placeholder_record = type('obj', (object,), {
                                    'register': type('obj', (object,), {'date': current_date_obj}),
                                    'status': 'Holiday',
                                    'is_holiday': True,
                                    'holiday_name': holiday_info['name'],
                                    'is_auto_holiday': holiday_info['is_auto'],
                                    'leave_status': None,
                                    'leave_subject': None,
                                    'leave_reason': None,
                                    'leave_attachment': None,
                                    'has_data': True  
                                })()
                                all_records.append(placeholder_record)
                            else:
                                leave_info = leave_map.get((student.id, current_date_obj))
                                if leave_info:
                                    placeholder_record = type('obj', (object,), {
                                        'register': type('obj', (object,), {'date': current_date_obj}),
                                        'status': 'Absent',
                                        'is_holiday': False,
                                        'holiday_name': None,
                                        'is_auto_holiday': False,
                                        'leave_status': leave_info["status"],
                                        'leave_subject': leave_info["subject"],
                                        'leave_reason': leave_info["reason"],
                                        'leave_attachment': leave_info["attachment"],
                                        'has_data': True  
                                    })()
                                    all_records.append(placeholder_record)
                                else:
                                    placeholder_record = type('obj', (object,), {
                                        'register': type('obj', (object,), {'date': current_date_obj}),
                                        'status': None, 
                                        'is_holiday': False,
                                        'holiday_name': None,
                                        'is_auto_holiday': False,
                                        'leave_status': None,
                                        'leave_subject': None,
                                        'leave_reason': None,
                                        'leave_attachment': None,
                                        'has_data': False 
                                    })()
                                    all_records.append(placeholder_record)
            
                    present_count = len([r for r in all_records if getattr(r, 'status', None) == 'Present'])
                    absent_count = len([r for r in all_records if getattr(r, 'status', None) == 'Absent'])
                    holiday_count = len([r for r in all_records if getattr(r, 'is_holiday', False)])
                    
                    attendance_by_student[student.id] = {
                        "records": all_records,
                        "total_present": present_count,
                        "total_absent": absent_count,
                        "total_holiday": holiday_count,
                    }

                today_attendance_present = today_attendance.filter(status="Present").select_related("student")
                today_attendance_absent = today_attendance.filter(status="Absent").select_related("student")

                today_is_manual_holiday = Holiday.objects.filter(
                    is_active=True,
                    date=today
                ).filter(
                    Q(scope='all') | Q(branch=teacher.branch)
                ).exists()
                
                today_is_auto_holiday, today_holiday_name = Holiday.is_auto_holiday(today)
                today_is_holiday = today_is_manual_holiday or today_is_auto_holiday

                import calendar
                days_in_selected_month = calendar.monthrange(selected_year, selected_month)[1]
                days_in_month = [f"{day:02d}" for day in range(1, days_in_selected_month + 1)]

                months_list = [
                    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
                    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
                    (9, "September"), (10, "October"), (11, "November"), (12, "December")
                ]

                current_year = current_date.year
                available_years = list(range(current_year - 5, current_year + 2))

                batches = (
                    Batch.objects.filter(
                        is_active=True,
                        status="in_progress",
                        branch=teacher.branch,
                        course=teacher.course,
                    )
                    .annotate(student_count=Count("admission", filter=Q(admission__is_active=True, admission__stage_status="active")))
                    .filter(student_count__gte=1)
                )

                context.update({
                    "attendance_by_student": attendance_by_student,
                    "students_by_batch": students_by_batch,
                    "today_present_count": today_attendance_present.count(),
                    "today_absent_count": today_attendance_absent.count(),
                    "today_attendance_present": today_attendance_present,
                    "today_attendance_absent": today_attendance_absent,
                    "today_is_holiday": today_is_holiday,
                    "today_holiday_name": today_holiday_name if today_is_auto_holiday else None,
                    "days_in_month": days_in_month,
                    "teacher_branch": teacher.branch,
                    "teacher_course": teacher.course.name,
                    "student_count": student_list.count(),
                    "months_list": months_list,
                    "available_years": available_years,
                    "current_month": selected_month,
                    "current_year": selected_year,
                    "batches": batches,
                    "holiday_dates": holiday_map,
                })
        
        elif user.is_superuser or user.usertype in ["admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "partner"]:
            context["branch_count"] = Branch.objects.filter(is_active=True).count() or 0
            context["total_employee_count"] = Employee.objects.count()
            context["active_student_count"] = Admission.objects.filter(stage_status="active", is_active=True).count()
            context["offline_students_count"] = Admission.objects.filter(is_active=True, course_mode="offline").count()
            context["totel_students_count"] = Admission.objects.count()
            context["online_students_count"] = Admission.objects.filter(is_active=True, course_mode="online").count()
            context["total_course_count"] = Course.objects.count()
            context["demo_leads"] = AdmissionEnquiry.objects.filter(status="demo", is_active=True).count()
            context["incomplete_requests"] = RequestSubmission.objects.filter(is_active=True, is_request_completed="false").order_by('-created')
            context["total_partners_count"] = Partner.objects.count()
            context["company_profile"] = CompanyProfile.objects.first()
            context["partners"] = Partner.objects.all().order_by('-shares_owned')
            
            branch_infos = Branch.objects.filter(is_active=True).annotate(
                student_count=Count(
                    "admission",
                    filter=Q(admission__is_active=True, admission__stage_status="active"),
                    distinct=True
                ),
                employee_count=Count(
                    "employee",
                    distinct=True,
                    filter=Q(employee__is_active=True, employee__user__is_superuser=False, employee__status="Appointed")
                )
            )

            branch_infos = list(branch_infos)

            for branch in branch_infos:
                # --- UPDATED: Branch-specific Finance Calculation ---
                # Removed is_active=True and used FINANCIAL_STAGES
                students = Admission.objects.filter(
                    branch=branch,
                    stage_status__in=FINANCIAL_STAGES
                ).select_related("course")

                total_fee_paid = Decimal('0.00')
                total_fee_amount = Decimal('0.00')

                for student in students:

                    total_paid = FeeReceipt.objects.filter(
                        student=student, 
                        is_active=True
                    ).aggregate(
                        total=Sum('payment_methods__amount')
                    )['total'] or Decimal('0.00')
                    total_fee_paid += total_paid

                    course_fee = FeeStructure.objects.filter(
                        student=student,
                        is_active=True
                    ).aggregate(
                        total=Sum('amount')
                    )['total'] or Decimal('0.00')
                    total_fee_amount += course_fee

                pending = total_fee_amount - total_fee_paid
                branch.total_fee_amount = total_fee_amount
                branch.total_fee_paid = total_fee_paid
                branch.pending_fee_amount = pending if pending > 0 else Decimal('0.00')
                
                # Seat calculations remain on active students only (usually)
                forenoon_occupied = Admission.objects.filter(
                    branch=branch,
                    batch_type='forenoon',
                    stage_status='active'
                ).count()
                afternoon_occupied = Admission.objects.filter(
                    branch=branch,
                    batch_type='afternoon',
                    stage_status='active'
                ).count()
                evening_occupied = Admission.objects.filter(
                    branch=branch,
                    batch_type='evening',
                    stage_status='active'
                ).count()

                branch.forenoon_available = branch.seating_capacity - forenoon_occupied if branch.seating_capacity else 0
                branch.afternoon_available = branch.seating_capacity - afternoon_occupied if branch.seating_capacity else 0
                branch.evening_available = branch.seating_capacity - evening_occupied if branch.seating_capacity else 0

                branch.forenoon_occupied = forenoon_occupied
                branch.afternoon_occupied = afternoon_occupied
                branch.evening_occupied = evening_occupied

            context["branch_infos"] = branch_infos

            
        elif user.usertype == "branch_staff":
            branch = user.branch 

            # --- UPDATED: Branch Staff Finance Calculation ---
            # Removed is_active=True and used FINANCIAL_STAGES
            students_in_branch = Admission.objects.filter(
                branch=branch,
                stage_status__in=FINANCIAL_STAGES,
            ).select_related("course")

            total_balance = Decimal('0.00')
            total_credited = Decimal('0.00')

            for student in students_in_branch:
                paid = FeeReceipt.objects.filter(
                    student=student, 
                    is_active=True
                ).aggregate(
                    total=Sum('payment_methods__amount')
                )['total'] or Decimal('0.00')

                total_credited += paid

                if student.course and student.course.fees:
                    course_fee = student.course.fees
                    if student.discount_amount:
                        course_fee -= student.discount_amount
                else:
                    course_fee = Decimal('0.00')

                pending = course_fee - paid

                if pending > 0:
                    total_balance += pending

            my_request = RequestSubmission.objects.filter(
                branch=branch, creator=user, is_active=True
            )

            context["branch"] = branch
            context["employee_count"] = Employee.objects.filter(branch=branch, is_active=True).count()
            context["student_count"] = students_in_branch.count()
            context["total_balance"] = total_balance
            context["total_credited"] = total_credited
            context['demo_leads'] = AdmissionEnquiry.objects.filter(status="demo", branch=branch, is_active=True).count()
            context['my_request_count'] = my_request.count()
            context['my_approved_request_count'] = my_request.filter(status="approved", current_usertype=user.usertype).count()
            context['my_rejected_request_count'] = my_request.filter(status="rejected", current_usertype=user.usertype).count()

        elif user.usertype == "mentor":
            branch = user.branch 
            students = Admission.objects.filter(is_active=True, stage_status="active",)
            branches = Branch.objects.all().annotate(
                student_count=Count(
                    'admission',
                    filter=Q(admission__is_active=True, admission__stage_status="active"),
                     distinct=True
                )
            )

            context["branch"] = branch
            context["employee_count"] = Employee.objects.filter(branch=branch, is_active=True).count()
            context["student_count"] = students.count()
            context['branch_list'] = branches

        elif user.usertype == "sales_head":
            active_enquiries = AdmissionEnquiry.objects.filter(is_active=True)
            branch = user.branch 
            students_in_branch = Admission.objects.filter(branch=branch, is_active=True, stage_status="active",)

            context['my_leads'] = active_enquiries.filter(tele_caller=self.request.user.employee).count()
            context['awaiting_leads'] = active_enquiries.filter(tele_caller__isnull=True).count()
            context["assigned_lead_count"] = active_enquiries.filter(tele_caller__isnull=False).count()
            context["tele_callers_count"] = Employee.objects.filter(user__usertype="tele_caller", is_active=True).count()
            context['total_enquiries'] = active_enquiries.count()
            context['enquiry_type_counts'] = active_enquiries.values('enquiry_type').annotate(count=Count('id'))
            context['branch_counts'] = active_enquiries.values('branch__id', 'branch__name').annotate(count=Count('id'))
            context['course_counts'] = active_enquiries.values('course__id', 'course__name').annotate(count=Count('id'))
            context['status_counts'] = active_enquiries.values('status').annotate(count=Count('id'))

        elif user.usertype == "tele_caller":
            branch = user.branch 
            students_in_branch = Admission.objects.filter(branch=branch, is_active=True, stage_status="active",)

            today = datetime.now().date()
            today_enquiries_qs = AdmissionEnquiry.objects.filter(
                tele_caller=self.request.user.employee,
                next_enquiry_date=today
            )

            table = AdmissionEnquiryTable(today_enquiries_qs)
            RequestConfig(self.request, paginate={"per_page": 10}).configure(table)

            branch_infos = Branch.objects.filter(is_active=True).annotate(
                student_count=Count(
                    "admission",
                    filter=Q(admission__is_active=True, admission__stage_status="active"),
                    distinct=True
                ),
                employee_count=Count(
                    "employee",
                    distinct=True,
                    filter=Q(employee__is_active=True, employee__user__is_superuser=False, employee__status="Appointed")
                )
            )

            branch_infos = list(branch_infos)

            for branch in branch_infos:
                # --- UPDATED: Telecaller Branch Finance Calculation ---
                # Removed is_active=True and used FINANCIAL_STAGES
                students = Admission.objects.filter(
                    branch=branch,
                    stage_status__in=FINANCIAL_STAGES
                ).select_related("course")

                total_pending_amount = Decimal('0.00')
                total_fee_paid = Decimal('0.00')
                total_fee_amount = Decimal('0.00')

                for student in students:
                    total_paid = FeeReceipt.objects.filter(
                        student=student, 
                        is_active=True
                    ).aggregate(
                        total=Sum('payment_methods__amount')
                    )['total'] or Decimal('0.00')
                    
                    total_fee_paid += total_paid

                    course_fee = Decimal('0.00')
                    if student.course and student.course.fees:
                        course_fee = student.course.fees

                        if student.discount_amount:
                            course_fee -= student.discount_amount
                    
                    total_fee_amount += course_fee

                    pending_amount = course_fee - total_paid

                    if pending_amount > 0:
                        total_pending_amount += pending_amount

                branch.pending_fee_amount = total_pending_amount
                branch.total_fee_paid = total_fee_paid
                branch.total_fee_amount = total_fee_amount
                
                forenoon_occupied = Admission.objects.filter(
                    branch=branch,
                    batch_type='forenoon',
                    stage_status='active'
                ).count()
                afternoon_occupied = Admission.objects.filter(
                    branch=branch,
                    batch_type='afternoon',
                    stage_status='active'
                ).count()
                evening_occupied = Admission.objects.filter(
                    branch=branch,
                    batch_type='evening',
                    stage_status='active'
                ).count()

                branch.forenoon_available = branch.seating_capacity - forenoon_occupied if branch.seating_capacity else 0
                branch.afternoon_available = branch.seating_capacity - afternoon_occupied if branch.seating_capacity else 0
                branch.evening_available = branch.seating_capacity - evening_occupied if branch.seating_capacity else 0
                
                branch.forenoon_occupied = forenoon_occupied
                branch.afternoon_occupied = afternoon_occupied
                branch.evening_occupied = evening_occupied

            context["branch_infos"] = branch_infos
            context['total_my_leads'] = AdmissionEnquiry.objects.filter(tele_caller=self.request.user.employee).count()
            context['awaiting_leads'] = AdmissionEnquiry.objects.filter(tele_caller__isnull=True).count()
            context["student_count"] = students_in_branch.count()
            context["employee_count"] = Employee.objects.filter(branch=branch, is_active=True).count()
            context["today_enquiries"] = today_enquiries_qs
            context["table"] = table
            context["today_date"] = datetime.now().date()
            context['branch_counts'] = AdmissionEnquiry.objects.values('branch__id', 'branch__name').annotate(count=Count('id'))
            context['course_counts'] = AdmissionEnquiry.objects.values('course__id', 'course__name').annotate(count=Count('id'))
            context['status_counts'] = AdmissionEnquiry.objects.values('status').annotate(count=Count('id'))
            context['enquiry_type_counts'] = AdmissionEnquiry.objects.values('enquiry_type').annotate(count=Count('id'))

        return context



class IDCardView(PDFView):
    pdfkit_options = {
        "page-height": "3.534in",
        "page-width": "1.9690in",
        "encoding": "UTF-8",
        "margin-top": "0",
        "margin-bottom": "0",
        "margin-left": "0",
        "margin-right": "0",
    }

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")

        if pk:
            try:
                self.instance = Admission.objects.get(pk=pk)
                self.template_name = "core/student_id_card.html"
            except Admission.DoesNotExist:
                self.instance = get_object_or_404(Employee, pk=pk)
                self.template_name = "core/id_card.html"
        else:
            if request.user.usertype == "student":
                self.instance = get_object_or_404(Admission, user=request.user)
                self.template_name = "core/student_id_card.html"
            else:
                self.instance = get_object_or_404(Employee, user=request.user)
                self.template_name = "core/id_card.html"

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if isinstance(self.instance, Admission):
            student = self.instance
            if student.photo:
                photo_url = self.request.build_absolute_uri(student.photo.url)
            else:
                photo_url = f"https://ui-avatars.com/api/?name={student.first_name}&background=fdc010&color=fff&size=128"
            context["qr_code_image"] = generate_qr_code_base64(self.request.build_absolute_uri(student.get_profile_url()))
        else:
            employee = self.instance
            if hasattr(employee, 'photo') and employee.photo:
                photo_url = self.request.build_absolute_uri(employee.photo.url)
            else:
                photo_url = f"https://ui-avatars.com/api/?name={employee.fullname}&background=fdc010&color=fff&size=128"
            context["qr_code_image"] = None

        context["title"] = "ID Card"
        context["instance"] = self.instance
        context["photo_url"] = photo_url
        return context

    def render_html(self, *args, **kwargs):
        static_url = f"{self.request.scheme}://{self.request.get_host()}{settings.STATIC_URL}"
        media_url = f"{self.request.scheme}://{self.request.get_host()}{settings.MEDIA_URL}"

        with override_settings(STATIC_URL=static_url, MEDIA_URL=media_url):
            template = loader.get_template(self.get_template_names())
            context = self.get_context_data(*args, **kwargs)
            return template.render(context)

    def get_filename(self):
        return "id_card.pdf"

    
def generate_qr_code_base64(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()  


class ServiceWorkerView(View):
    def get(self, request, *args, **kwargs):
        sw_path = finders.find('firebase-messaging-sw.js')
        if not sw_path or not os.path.exists(sw_path):
            return HttpResponseNotFound('Service worker not found')

        with open(sw_path, 'rb') as f:
            data = f.read()

        response = HttpResponse(data, content_type='application/javascript')
        response['Service-Worker-Allowed'] = '/'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    
class CompanyProfileView(mixins.HybridTemplateView):
    template_name = "core/company/company_profile.html"
    permissions = ['is_superuser']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = CompanyProfile.objects.filter(is_active=True).first()
        return context
        

class CompanyProfileCreateView(mixins.HybridCreateView):
    model = CompanyProfile
    fields = ['name', 'total_value', 'number_of_shares', 'company_hold_shares']
    template_name = "core/company/company_profile_form.html"
    permissions = ['is_superuser']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = CompanyProfile.objects.filter(is_active=True).first()
        return context
    
    def form_valid(self, form):
        existing_active_company = CompanyProfile.objects.filter(is_active=True).first()
        if existing_active_company:
            messages.error(self.request, "An active company already exists. Please deactivate it before creating a new one.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("core:company_profile")


class CompanyProfileUpdateView(mixins.HybridUpdateView):
    model = CompanyProfile
    template_name = "core/company/company_profile_form.html"
    fields = ['name', 'total_value', 'number_of_shares', 'company_hold_shares']
    permissions = ['is_superuser']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = CompanyProfile.objects.filter(is_active=True).first()
        return context

    
class CompanyProfileDeleteView(mixins.HybridDeleteView):
    model = CompanyProfile
    permissions = ['is_superuser']