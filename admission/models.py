import os
import re
import uuid
from decimal import Decimal
from django.core.validators import RegexValidator
from django.db.models import Max
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from django.utils.functional import cached_property
    
from core.base import BaseModel
from django.db import models

from core.choices import BATCH_TYPE_CHOICES, BLOOD_CHOICES, BOOL_CHOICES, CHOICES, FEE_STRUCTURE_TYPE, FEE_TYPE, INSTALLMENT_TYPE_CHOICES, MARITAL_CHOICES, PAYMENT_METHOD_CHOICES
from core.choices import GENDER_CHOICES
from core.choices import RELIGION_CHOICES, COURSE_MODE_CHOICES
from core.choices import PAYMENT_PERIOD_CHOICES
from core.choices import ATTENDANCE_STATUS, STUDENT_STAGE_STATUS_CHOICES, PLACEMENT_SOURCE_CHOICES
from core.choices import MONTH_CHOICES, ENQUIRY_TYPE_CHOICES, ENQUIRY_STATUS

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from datetime import datetime

from admission.utils import send_sms
from masters.models import LeaveRequest, PlacementRequest

phone_validator = RegexValidator(
    regex=r'^91\d{10}$',
    message='Enter number in international format like 91987654321 (no + or spaces).'
)

def generate_admission_no(course):
    first_letter = course.name[0].upper() if course and course.name else 'X'
    prefix = f"OX{first_letter}"
    last_admission = Admission.objects.filter(admission_number__startswith=prefix).order_by('-admission_number').first()

    if last_admission and last_admission.admission_number:
        try:
            last_number = int(last_admission.admission_number.replace(prefix, ""))
            next_number = last_number + 1
        except ValueError:
            next_number = 1
    else:
        next_number = 1

    return f"{prefix}{str(next_number).zfill(3)}"


def generate_receipt_no(student):
    # Get the branch name from the student instance
    branch_name = student.branch.name

    # Function to generate branch code dynamically
    def get_branch_code(name):
        code = re.sub(r'[AEIOUaeiou\s]', '', name)[:3].upper()
        return code.ljust(3, 'X')  # pad with 'X' if less than 3 characters

    branch_code = get_branch_code(branch_name)
    
    # Find the max receipt number for this branch
    max_receipt_no = FeeReceipt.objects.filter(student__branch=student.branch).aggregate(Max('receipt_no'))['receipt_no__max']

    if max_receipt_no is None:
        next_no = 1
    else:
        # Extract numeric part from the receipt number
        numeric_part = re.findall(r'\d+$', max_receipt_no)
        next_no = int(numeric_part[0]) + 1 if numeric_part else 1

    # Construct the new receipt number
    receipt_no = f"OXD{branch_code}{str(next_no).zfill(3)}"
    return receipt_no


def active_objects():
    return {'is_active': True}


class Admission(BaseModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name="student",null=True, )
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE) 
    first_name = models.CharField(max_length=200,null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    joining_date = models.DateField(null=True)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    blood_group = models.CharField(max_length=20,choices=BLOOD_CHOICES, blank=True, null=True)
    religion = models.CharField(max_length=20, choices=RELIGION_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=128, choices=MARITAL_CHOICES, blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    passout_year = models.CharField(max_length=10, blank=True, null=True)
    cgpa_or_percentage = models.CharField(max_length=20, blank=True, null=True)
    course_mode = models.CharField(max_length=125, choices=COURSE_MODE_CHOICES, default="offline")
    
    home_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=180, blank=True, null=True)
    district = models.CharField(max_length=180, blank=True, null=True)
    state = models.CharField(max_length=180, blank=True, null=True)
    pin_code = models.CharField(max_length=180, blank=True, null=True)
    
    personal_email = models.EmailField(null=True, unique=True)
    contact_number = models.CharField(max_length=30,null=True,)
    whatsapp_number = models.CharField(max_length=30,null=True,)
    
    admission_number = models.CharField(max_length=10, null=True, blank=True)
    admission_date = models.DateField(default=timezone.now)
    course_start_date = models.DateField(null=True)
    photo = models.FileField(upload_to="admission/documents/", null=True, blank=True)
    
    course = models.ForeignKey('masters.Course', on_delete=models.CASCADE, limit_choices_to={"is_active": True}, null=True,)
    batch = models.ForeignKey('masters.Batch',on_delete= models.CASCADE,limit_choices_to={"is_active": True}, null=True)
    batch_type = models.CharField(max_length=30, choices=BATCH_TYPE_CHOICES, default="forenoon")
    other_details = models.TextField(blank=True, null=True)
    care_of = models.ForeignKey('accounts.User', limit_choices_to=active_objects(), on_delete=models.SET_NULL, null=True, blank=True)
    document = models.FileField(upload_to="admission/documents/", null=True, blank=True)
    signature = models.FileField(upload_to="admission/signature/", null=True, blank=True)
    
    # Parent Info
    parent_first_name = models.CharField(max_length=200,null=True,)
    parent_last_name = models.CharField(max_length=200, blank=True, null=True)
    parent_contact_number = models.CharField(max_length=12, null=True, validators=[phone_validator], help_text="Enter Contact number with country code, e.g. 91987654321")
    parent_whatsapp_number = models.CharField(max_length=12, null=True, validators=[phone_validator],help_text="Enter WhatsApp number with country code, e.g. 91987654321")
    parent_mail_id = models.EmailField(verbose_name="Mail Id", null=True, blank=True)
    parent_signature = models.FileField(
        upload_to="admission/parent_signature/", null=True, blank=True
    )
    
    # finance
    fee_type = models.CharField(max_length=30, choices=FEE_TYPE, blank=True, null=True)
    installment_type = models.CharField(max_length=30, choices=INSTALLMENT_TYPE_CHOICES, blank=True, null=True)
    custom_installment_months = models.PositiveIntegerField(null=True, blank=True, help_text="Enter number of months for custom installment")
    discount_amount = models.PositiveIntegerField(null=True, blank=True)
    admission_fee_amount = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    admission_fee_payment_type = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    account = models.OneToOneField('accounting.Account', on_delete=models.CASCADE, null=True, blank=True)
    
    stage_status = models.CharField(max_length=180, choices=STUDENT_STAGE_STATUS_CHOICES, default="active")

    # Placement Details
    placed_company_name = models.CharField(max_length=255, blank=True, null=True)
    placed_position = models.CharField(max_length=255, blank=True, null=True)
    placement_source = models.CharField(
        max_length=30,
        choices=PLACEMENT_SOURCE_CHOICES,
        blank=True,
        null=True,
        help_text="How the student got placed or internship"
    )
    
    def fullname(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def parentfullname(self):
        if self.parent_last_name:
            return f"{self.parent_first_name} {self.parent_last_name}"
        return self.parent_first_name
    
    def age(self):
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year
        
    def __str__(self):
        return f"{self.fullname()} - {self.admission_number}"

    @staticmethod
    def get_list_url():
        return reverse_lazy("admission:admission_list")

    def get_absolute_url(self):
        return reverse_lazy("admission:admission_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("admission:admission_update", kwargs={"pk": self.pk})
    
    def get_admission_url(self):
        return reverse_lazy("admission:admission_create", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("admission:admission_delete", kwargs={"pk": self.pk})

    def get_id_card_absolute_url(self):
        return reverse_lazy("core:id_card", kwargs={"pk": self.pk})
    
    def get_profile_url(self):
        return reverse_lazy("admission:admission_profile_detail", kwargs={"pk": self.pk})
    
    @staticmethod
    def get_fee_overview_list_url():
        return reverse_lazy("admission:student_fee_overview_list")
    
    def get_fee_overview_absolute_url(self):
        return reverse_lazy("admission:student_fee_overview_detail", kwargs={"pk": self.pk})
    
    def get_placement_history_create_url(self):
        return reverse_lazy("masters:placement_history_create", kwargs={"pk": self.pk})

    def get_student_syllabus_report_url(self):
        return reverse_lazy("masters:student_syllabus_report", kwargs={"pk": self.pk})

    @cached_property
    def is_student_send_placement_request(self):
        return PlacementRequest.objects.filter(student=self).exists()
    
    def clean(self):
        if self.fee_type == "installment":
            if not self.installment_type:
                raise ValidationError("Installment type is required")
            
            if self.installment_type == "custom" and not self.custom_installment_months:
                raise ValidationError({"custom_installment_months": "Number of months is required for Custom Installment."})
    
    def create_fee_structure(self):
        if not self.course:
            return

        # 1. Setup Amounts
        total_fee = Decimal(str(self.course.fees))
        discount = Decimal(str(self.discount_amount or 0))
        admission_fee = Decimal(str(self.admission_fee_amount or 0))
        start_date = self.course_start_date or timezone.now().date()

        # 2. Calculate Net Amount (Tuition Only)
        # Logic: Course Fee - Discount - Admission Fee
        net_amount = total_fee - discount - admission_fee
        if net_amount < 0:
            net_amount = Decimal('0.00')

        # 3. Calculate Previously Paid (Excluding Admission Fee)
        receipts = FeeReceipt.objects.filter(
            student=self, is_active=True
        ).exclude(note="Admission Fee").order_by('date')
        total_paid = sum(Decimal(str(r.get_amount())) for r in receipts)

        # 4. Clear old structure
        FeeStructure.objects.filter(student=self).delete()

        # ===============================
        # INSTALLMENT LOGIC
        # ===============================
        if self.fee_type == "installment":
            amounts = []

            # -------- REGULAR (Fixed 4 Months) --------
            if self.installment_type == "regular":
                num_installments = 4
                installment_amount = (net_amount / num_installments).quantize(Decimal('0.01'))
                amounts = [installment_amount] * num_installments
                
                # Fix rounding
                allocated = installment_amount * num_installments
                if allocated != net_amount:
                    amounts[-1] += net_amount - allocated

            # -------- SPECIAL (Fixed ₹5500 Amount) --------
            elif self.installment_type == "special":
                installment_amount = Decimal('5500.00')
                if net_amount > 0:
                    num_installments = (net_amount + installment_amount - Decimal('1.00')) // installment_amount
                    num_installments = max(1, int(num_installments))
                else:
                    num_installments = 0
                
                remaining = net_amount
                for i in range(num_installments):
                    if i == num_installments - 1:
                        amounts.append(remaining)
                    else:
                        amounts.append(installment_amount)
                        remaining -= installment_amount

            # -------- CUSTOM (Dynamic Months) - YOUR NEW LOGIC --------
            elif self.installment_type == "custom":
                # Get months from field, default to 1 to avoid division by zero
                num_installments = self.custom_installment_months or 1 
                
                # Calculate: (Total - Discount - Adm Fee) / Months
                installment_amount = (net_amount / num_installments).quantize(Decimal('0.01'))
                
                amounts = [installment_amount] * num_installments

                # Fix rounding (e.g., if 100 / 3 = 33.33, 33.33, 33.34)
                allocated = installment_amount * num_installments
                if allocated != net_amount:
                    diff = net_amount - allocated
                    amounts[-1] += diff

            # 5. Create Records
            for i, amt in enumerate(amounts, start=1):

                # Rule:
                # Before 20 → same month
                # On/After 20 → next month
                if start_date.day < 20:
                    first_month_offset = 0
                else:
                    first_month_offset = 1

                base_date = start_date.replace(day=1)
                future_date = base_date + relativedelta(
                    months=first_month_offset + (i - 1)
                )

                payment_date = future_date.replace(day=5)
                due_date = future_date.replace(day=10)

                # Allocate previous payments
                paid_for_this = Decimal('0.00')
                if total_paid > 0:
                    paid_for_this = min(total_paid, amt)
                    total_paid -= paid_for_this

                FeeStructure.objects.create(
                    student=self,
                    installment_no=i,
                    name=f"Installment {i}",
                    amount=amt,
                    paid_amount=paid_for_this,
                    is_paid=paid_for_this >= amt,
                    payment_date=payment_date,
                    due_date=due_date,
                )

        # ===============================
        # ONE-TIME / FINANCE
        # ===============================
        elif self.fee_type in ["one_time", "finance"]:

            if net_amount > 0:
                paid_amount = min(total_paid, net_amount)

                FeeStructure.objects.create(
                    student=self,
                    installment_no=1,
                    name="Full Payment",
                    amount=net_amount,
                    paid_amount=paid_amount,
                    is_paid=paid_amount >= net_amount,
                    payment_date=start_date,
                    due_date=start_date,
                )
    
    def save(self, *args, **kwargs):
        # 1. Auto-generate admission number
        if not self.admission_number and self.course:
            self.admission_number = generate_admission_no(self.course)

        # 2. Rename uploaded photo
        if not self.pk and self.photo:
            self.photo.name = f"{uuid.uuid4()}{os.path.splitext(self.photo.name)[1]}"

        # 3. Manage User active status
        if self.user:
            self.user.is_active = self.stage_status == "active"
            self.user.save(update_fields=["is_active"])

        # 4. SAVE THE INSTANCE FIRST (To ensure we have the latest data)
        super().save(*args, **kwargs)

        # 5. Handle Admission Fee Receipt (Create OR Update)
        if self.admission_fee_amount is not None:
            # Check if a receipt already exists for Admission Fee
            existing_receipt = FeeReceipt.objects.filter(
                student=self, note="Admission Fee", is_active=True
            ).first()

            if existing_receipt:
                # UPDATE EXISTING: If receipt exists, update the amount in PaymentMethod
                # We assume 1 receipt has 1 payment method for admission fee
                payment_method = PaymentMethod.objects.filter(fee_receipt=existing_receipt).first()
                if payment_method:
                    # Only update if the amount has actually changed to avoid redundancy
                    if payment_method.amount != self.admission_fee_amount:
                        payment_method.amount = self.admission_fee_amount
                        payment_method.payment_type = self.admission_fee_payment_type
                        payment_method.save()
                        
                        # Optionally update receipt date if course start date changed
                        existing_receipt.date = self.course_start_date or timezone.now().date()
                        existing_receipt.save()
            
            elif self.admission_fee_amount > 0:
                # CREATE NEW: If no receipt exists and amount > 0
                fee_receipt = FeeReceipt.objects.create(
                    student=self,
                    receipt_no=f"ADM{self.pk:04d}",
                    date=self.admission_date or timezone.now().date(),
                    note="Admission Fee",
                    status='paid'
                )
                
                PaymentMethod.objects.create(
                    fee_receipt=fee_receipt,
                    payment_type=self.admission_fee_payment_type,
                    amount=self.admission_fee_amount,
                    note="Admission Fee Payment"
                )

        if self.fee_type in ["installment", "one_time", "finance"]:
            self.create_fee_structure()

    def get_total_fee_amount(self):
        """Get total amount paid by student (including admission fee)"""
        from django.db.models import Sum
        total_paid = PaymentMethod.objects.filter(
            fee_receipt__student=self,
            fee_receipt__is_active=True
        ).aggregate(
            total_amount=Sum('amount')
        )['total_amount'] or Decimal('0.00')
        return Decimal(str(total_paid))
    
    def get_balance_amount(self):
        """Get remaining balance - based on course fee minus discount and total paid"""
        if not self.course:
            return Decimal('0.00')
        
        course_fee = Decimal(str(self.course.fees))
        discount = Decimal(str(self.discount_amount or 0))
        total_paid = self.get_total_fee_amount()
        
        net_amount = course_fee - discount
        return net_amount - total_paid

    def get_current_fee(self):
        """Get current net fee after discount"""
        if not self.course:
            return Decimal('0.00')
        course_fee = Decimal(str(self.course.fees))
        discount = Decimal(str(self.discount_amount or 0))
        return course_fee - discount
    
    def get_fee(self):
        return FeeStructure.objects.filter(course=self.course)
    
    def get_latest_stage_remark(self):
        """Get the latest remark from StudentStageStatusHistory"""
        latest_history = self.studentstagestatushistory_set.order_by('-created').first()
        return latest_history.remark if latest_history else ""
    
    def get_placement_status(self):
        if self.placementhistory_set.filter(joining_status='yes').exists():
            return "Placed"
        elif self.placementhistory_set.exists():
            return "Interviewed"
        else:
            return "Pending"
    
    def get_pending_subscriptions(self):
        """Get all fee structures that should show subscription popup"""
        today = timezone.now().date()
        
        pending_fees = FeeStructure.objects.filter(
            student=self,
            is_paid=False
        ).exclude(
            due_date__isnull=True
        ).order_by('due_date')
        
        return [fee for fee in pending_fees if fee.should_show_subscription_popup()]

    def get_current_month_subscription(self):
        """Get current month's subscription for popup display"""
        pending_fees = self.get_pending_subscriptions()
        if pending_fees:
            return pending_fees[0]  # Return the most urgent one
        return None

    def has_active_subscription(self):
        """Check if student has any active subscription (all fees paid for current period)"""
        current_month = timezone.now().date().month
        current_year = timezone.now().date().year
        
        current_month_fees = FeeStructure.objects.filter(
            student=self,
            due_date__year=current_year,
            due_date__month=current_month,
            is_paid=False
        )
        
        return not current_month_fees.exists()

    def get_subscription_overview(self):
        """Get complete subscription overview for display"""
        total_fees = FeeStructure.objects.filter(student=self)
        paid_fees = total_fees.filter(is_paid=True)
        pending_fees = total_fees.filter(is_paid=False)
        overdue_fees = [fee for fee in pending_fees if fee.is_overdue()]
        current_month_fees = [fee for fee in pending_fees if fee.is_current_month_due()]
        
        return {
            'total_fees': total_fees.count(),
            'paid_fees': paid_fees.count(),
            'pending_fees': pending_fees.count(),
            'overdue_fees': len(overdue_fees),
            'current_month_fees': len(current_month_fees),
            'subscription_active': self.has_active_subscription(),
            'urgent_subscription': self.get_current_month_subscription(),
        }

    def get_fee_progress_data(self):
        total_to_pay = self.get_current_fee() # Course Fee - Discount
        total_paid = self.get_total_fee_amount()
        
        if total_to_pay <= 0:
            return {'percent': 0, 'color': 'danger', 'paid': 0, 'total': 0}
            
        percent = int((total_paid / total_to_pay) * 100)
        percent = min(percent, 100) # Cap at 100%
        
        # Determine color
        if percent >= 100: color = "success"
        elif percent >= 50: color = "info"
        elif percent >= 25: color = "warning"
        else: color = "danger"
            
        return {
            'percent': percent,
            'color': color,
            'paid': total_paid,
            'total': total_to_pay
        }
    

class StudentStageStatusHistory(BaseModel):
    student = models.ForeignKey(Admission, on_delete=models.CASCADE,limit_choices_to={'is_active': True,})
    status = models.CharField(max_length=180, choices=STUDENT_STAGE_STATUS_CHOICES, default="active")
    company_name = models.CharField(max_length=180, blank=True, null=True)
    position = models.CharField(max_length=180, blank=True, null=True)
    placement_source = models.CharField(max_length=180, choices=PLACEMENT_SOURCE_CHOICES, blank=True, null=True)
    remark = models.TextField()

    class Meta:
        verbose_name = 'Student Stage Status History'
        verbose_name_plural = 'Student Stage Status Histories'

    def __str__(self):
        return f"{self.student} - {self.status}"
    

class AttendanceRegister(BaseModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, limit_choices_to=active_objects, null=True)
    batch = models.ForeignKey("masters.Batch", on_delete=models.CASCADE, limit_choices_to=active_objects, null=True)
    date = models.DateField(null=True,)
    course = models.ForeignKey('masters.Course', on_delete=models.CASCADE, limit_choices_to={"is_active": True}, null=True,)
    
    def __str__(self):
        return f"{self.batch} - {self.date}"
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Batch Attendance Register"
        verbose_name_plural = "Batch Attendance Registers"
        
    def get_attendence(self):
        return Attendance.objects.filter(register=self)
    
    def get_total_attendence(self):
        return self.get_attendence().count()
    
    def get_total_present(self):
        return self.get_attendence().filter(status='Present').count()
    
    def get_total_absent(self):
        return self.get_attendence().filter(status='Absent').count()

    def get_absolute_url(self):
        return reverse_lazy("admission:attendance_register_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse_lazy("admission:attendance_register_list")

    def get_update_url(self):
        return reverse_lazy("admission:attendance_register_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("admission:attendance_register_delete", kwargs={"pk": self.pk})
    
    def is_holiday(self):
        """Check if this register date is a holiday"""
        from masters.models import Holiday
        return Holiday.objects.filter(
            is_active=True,
            date=self.date
        ).filter(
            Q(scope='all') | Q(branch=self.branch)
        ).exists()
    
    
class Attendance(BaseModel):
    register = models.ForeignKey(AttendanceRegister, on_delete=models.CASCADE)
    student = models.ForeignKey(Admission, on_delete=models.CASCADE, limit_choices_to={'is_active': True})
    login_time = models.TimeField(null=True, blank=True)
    logout_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=ATTENDANCE_STATUS, default='Absent')
    sms_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.fullname()} - {self.register.date} - {self.status}"

    def save(self, *args, **kwargs):
        if self.register and self.register.is_holiday():
            self.status = 'Holiday'
            self.sms_sent = True 
        
        is_new = self.pk is None
        was_absent = False
        
        if not is_new:
            try:
                old_instance = Attendance.objects.get(pk=self.pk)
                was_absent = old_instance.status == 'Absent'
            except Attendance.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

        if (self.status == 'Absent' and 
            (is_new or not was_absent) and 
            not self.sms_sent and
            not self.register.is_holiday()):
            
            self.send_absence_sms()
    
    def send_absence_sms(self):
        """Send SMS notification for absence"""
        phone_number = self.student.parent_whatsapp_number
        if not phone_number:
            return False
        
        try:
            has_leave = LeaveRequest.objects.filter(
                student=self.student,
                status='approved',
                start_date__lte=self.register.date,
                end_date__gte=self.register.date
            ).exists()

            if has_leave:
                message = (
                    f"*Oxdu Integrated Media School - Leave Notification / അവധി അറിയിപ്പ്*\n\n"
                    f"*English:*\n"
                    f"Dear Parent,\n\n"
                    f"This is to inform you that your child *{self.student.fullname()}* "
                    f"has an approved leave on *{self.date.strftime('%B %d, %Y')}*.\n"
                    f"Our records show that the leave request was submitted and approved.\n"
                    f"This message is just to confirm that you are aware of your child's leave.\n\n"
                    f"*Malayalam:*\n"
                    f"പ്രിയപ്പെട്ട രക്ഷിതാവേ,\n\n"
                    f"താങ്കളുടെ മകന്‍/മകളായ *{self.student.fullname()}* "
                    f"*{self.date.strftime('%Y-%m-%d')}* തീയതിയില്‍ അവധിയിലാണ്.\n"
                    f"അവധി അപേക്ഷ സമർപ്പിക്കുകയും അത് അംഗീകരിക്കുകയും ചെയ്തിട്ടുണ്ട്.\n"
                    f"താങ്കൾ ഈ അവധിയെക്കുറിച്ച് അറിയുന്നുവെന്ന് ഉറപ്പാക്കാനാണ് ഈ സന്ദേശം അയച്ചിരിക്കുന്നത്.\n\n"
                    f"Regards,\n"
                    f"*Oxdu Integrated Media School*"
                )
            else:
                message = (
                    f"*Oxdu Integrated Media School - Attendance Notification / ഹാജര്‍ അറിയിപ്പ്*\n\n"
                    f"*English:*\n"
                    f"Dear Parent,\n\n"
                    f"This is to inform you that your child *{self.student.fullname()}* "
                    f"was marked absent on *{self.date.strftime('%B %d, %Y')}*.\n"
                    f"If there is a valid reason for the absence, kindly inform the placement officer and the teacher.\n\n"
                    f"*Malayalam:*\n"
                    f"പ്രിയപ്പെട്ട രക്ഷിതാവേ,\n\n"
                    f"താങ്കളുടെ മകന്‍/മകളായ *{self.student.fullname()}* "
                    f"*{self.date.strftime('%Y-%m-%d')}* തീയതിയില്‍ ഹാജരായിരുന്നില്ല.\n"
                    f"ആയതിനാൽ യഥാർത്ഥ കാരണം, ദയവായി പ്ലേസ്മെന്റ് ഓഫീസറേയും അധ്യാപകനേയും അറിയിക്കുക.\n\n"
                    f"Regards,\n"
                    f"*Oxdu Integrated Media School*"
                )

            if send_sms(phone_number, message):
                self.sms_sent = True
                Attendance.objects.filter(pk=self.pk).update(sms_sent=True)
                return True
                
        except Exception as e:
            print(f"SMS sending failed: {str(e)}")
        
        return False

    class Meta:
        ordering = ['id']

    def get_absolute_url(self):
        return reverse_lazy("admission:attendance_register_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse_lazy("admission:attendance_register_list")

    def get_update_url(self):
        return reverse_lazy("admission:attendance_register_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("admission:attendance_register_delete", kwargs={"pk": self.pk})
        
    
class FeeStructure(BaseModel):
    student = models.ForeignKey("Admission", on_delete=models.CASCADE, null=True)
    installment_no = models.PositiveIntegerField(null=True, blank=True)  # 0 = Admission Fee
    name = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_structure'
    )
    
    # Subscription status tracking
    is_active_subscription = models.BooleanField(default=False)
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)

    # Razorpay subscription tracking
    razorpay_plan_id = models.CharField(max_length=64, blank=True, null=True)
    razorpay_subscription_id = models.CharField(max_length=64, blank=True, null=True)
    razorpay_status = models.CharField(max_length=32, blank=True, null=True)  # created/active/paused/completed

    def __str__(self):
        if self.name:
            return f"{self.student.fullname()} - {self.name} - {self.amount}"
        return f"{self.student.fullname()} - {self.amount}"

    def get_due_amount(self):
        amt = self.amount or Decimal(0)
        paid = self.paid_amount or Decimal(0)
        due = amt - paid
        return max(due, Decimal(0))

    def is_overdue(self):
        """Check if the fee is overdue"""
        if self.is_paid:
            return False
        return self.due_date and self.due_date < timezone.now().date()

    def is_current_month_due(self):
        """Check if due date is in current month"""
        if self.is_paid:
            return False
        today = timezone.now().date()
        return (self.due_date and 
                self.due_date.year == today.year and 
                self.due_date.month == today.month)

    def get_subscription_status(self):
        """Get subscription status for Hotstar-like display"""
        if self.is_paid:
            return "paid"
        elif self.is_overdue():
            return "overdue"
        elif self.is_current_month_due():
            return "due_this_month"
        else:
            return "upcoming"

    def should_show_subscription_popup(self):
        """Determine if subscription popup should be shown"""
        if self.is_paid:
            return False
        
        today = timezone.now().date()
        
        if self.is_overdue() or self.is_current_month_due():
            return True
        
        if self.due_date:
            days_until_due = (self.due_date - today).days
            return 0 <= days_until_due <= 7
            
        return False

    class Meta:
        verbose_name = "Student Fee Structure"
        verbose_name_plural = "Student Fee Structures"
        ordering = ["student", "installment_no"]
        
    
class FeeReceipt(BaseModel):
    student = models.ForeignKey("admission.Admission", on_delete=models.CASCADE, limit_choices_to={'is_active': True})
    receipt_no = models.CharField(max_length=10, null=True)
    date = models.DateField(null=True)
    note = models.CharField(max_length=128, blank=True, null=True)

    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Razorpay tracking
    razorpay_payment_id = models.CharField(max_length=64, blank=True, null=True)
    razorpay_subscription_id = models.CharField(max_length=64, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=256, blank=True, null=True)

    status = models.CharField(
        max_length=16,
        default='created',
        choices=(
            ('created', 'Created'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        )
    )

    def __str__(self):
        total_amount = self.get_amount()
        return f"Receipt No: {self.receipt_no} - Student: {self.student} - Amount: {total_amount}"

    def get_amount(self):
        """Get total amount from all payment methods"""
        from django.db.models import Sum
        total = self.payment_methods.aggregate(total_amount=Sum('amount'))['total_amount']
        return total or Decimal('0')

    def get_payment_types(self):
        """Get all payment types used in this receipt"""
        return list(self.payment_methods.values_list('payment_type', flat=True))

    def get_total_amount(self):
        """Get total amount paid by student across all receipts"""
        from django.db.models import Sum
        total_paid = FeeReceipt.objects.filter(
            student=self.student, 
            is_active=True
        ).annotate(
            receipt_total=Sum('payment_methods__amount')
        ).aggregate(
            total_amount=Sum('payment_methods__amount')
        )['total_amount'] or Decimal('0.00')
        return Decimal(str(total_paid))
    
    def get_balance_amount(self):
        """Get remaining balance after all receipts"""
        total_paid = self.get_total_amount()
        course_fee = Decimal(str(self.student.course.fees))
        discount = Decimal(str(self.student.discount_amount or 0))
        net_amount = course_fee - discount
        return net_amount - total_paid
    
    def get_receipt_balance(self):
        """Get balance after this specific receipt"""
        course_fee = Decimal(str(self.student.course.fees))
        discount = Decimal(str(self.student.discount_amount or 0))
        net_amount = course_fee - discount
        
        previous_payments = FeeReceipt.objects.filter(
            student=self.student, 
            id__lt=self.id,
            is_active=True
        ).annotate(
            receipt_total=Sum('payment_methods__amount')
        ).aggregate(
            total_amount=Sum('payment_methods__amount')
        )['total_amount'] or Decimal('0.00')
        
        previous_payments = Decimal(str(previous_payments))
        remaining_balance = net_amount - previous_payments
        receipt_amount = self.get_amount()
        receipt_balance = remaining_balance - receipt_amount  
        return max(receipt_balance, Decimal('0.00'))
    
    def get_due_amount(self):
        """Get due amount after this receipt"""
        return self.get_receipt_balance()
    
    def get_total_paid(self):
        return self.payment_methods.aggregate(
            total=Sum('amount')
        )['total'] or 0

    class Meta:
        ordering = ("-date",)
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("admission:fee_receipt_list")

    def get_absolute_url(self):
        return reverse_lazy("admission:fee_receipt_detail", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse_lazy("admission:fee_receipt_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("admission:fee_receipt_delete", kwargs={"pk": self.pk})
    

class PaymentMethod(models.Model):
    fee_receipt = models.ForeignKey("admission.FeeReceipt", on_delete=models.CASCADE, related_name="payment_methods")
    payment_type = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    note = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ["payment_type"]
        
    def __str__(self):
        return f"Payment Method: {self.payment_type} - Amount: {self.amount}"
    
    def get_absolute_url(self):
        return reverse_lazy('admission:fee_receipt_detail', kwargs={'pk': self.fee_receipt.pk})
    
    def get_update_url(self):
        return reverse_lazy("admission:payment_method_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("admission:payment_method_delete", kwargs={"pk": self.pk})

    def get_list_url(self):
        return reverse_lazy("admission:fee_receipt_list")
    

class AdmissionEnquiry(BaseModel):
    enquiry_type = models.CharField(max_length=80, choices=ENQUIRY_TYPE_CHOICES, default="public_lead")
    tele_caller = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=200, null=True)
    contact_number = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=180, blank=True, null=True)
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, limit_choices_to=active_objects, null=True, blank=True)
    course = models.ForeignKey('masters.Course', on_delete=models.CASCADE, limit_choices_to={"is_active": True}, null=True, blank=True)
    date = models.DateField(null=True)
    status = models.CharField(max_length=30, choices=ENQUIRY_STATUS, default="new_enquiry")
    next_enquiry_date = models.DateField(null=True, blank=True) 
    remark = models.TextField(blank=True, null=True)

    district = models.CharField(max_length=180, blank=True, null=True)
    state = models.CharField(max_length=180, blank=True, null=True)

    def str(self):
        return f"{self.full_name}"

    class Meta:
        ordering = ['-id']  
        verbose_name = 'Admission Enquiry'
        verbose_name_plural = 'Admission Enquiries'
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("admission:admission_enquiry")

    def get_absolute_url(self):
        return reverse_lazy("admission:admission_enquiry_detail", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse_lazy("admission:admission_enquiry_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("admission:admission_enquiry_delete", kwargs={"pk": self.pk})
    
    