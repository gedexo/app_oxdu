import datetime
from datetime import date
from django.utils import timezone
import calendar
import os
import uuid
from django.db import transaction
from decimal import Decimal
from django.db import transaction as db_transaction

from core.base import BaseModel
from core.choices import BLOOD_CHOICES, RELIGION_CHOICES
from core.choices import EMPLOYEE_STATUS_CHOICES
from core.choices import EMPLOYMENT_TYPE_CHOICES, LEAVE_STATUS_CHOICES
from core.choices import GENDER_CHOICES
from core.choices import MARITAL_CHOICES
from core.choices import RESIDENCE_CHOICES
from core.choices import YEAR_CHOICES, MONTH_CHOICES, PAYMENT_METHOD_CHOICES, PAYROLL_STATUS

from django.db import models
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from easy_thumbnails.fields import ThumbnailerImageField

from core.models import CompanyProfile

def current_year():
    return str(datetime.date.today().year)

def current_month():
    return str(datetime.date.today().month)

class Designation(BaseModel):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse_lazy("employees:designation_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:designation_list")

    @staticmethod
    def get_create_url():
        return reverse_lazy("employees:designation_create")

    def get_update_url(self):
        return reverse_lazy("employees:designation_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("employees:designation_delete", kwargs={"pk": self.pk})

    def __str__(self):
        return str(self.name)

    def employee_count(self):
        return self.employee_set.filter(is_active=True).count()


class Department(BaseModel):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    department_lead = models.ForeignKey("employees.Employee", on_delete=models.PROTECT, limit_choices_to={"is_active": True}, blank=True, null=True, related_name="department_lead")

    def get_absolute_url(self):
        return reverse_lazy("employees:department_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:department_list")

    @staticmethod
    def get_create_url():
        return reverse_lazy("employees:department_create")

    def get_update_url(self):
        return reverse_lazy("employees:department_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("employees:department_delete", kwargs={"pk": self.pk})

    def __str__(self):
        return str(self.name)

    def employee_count(self):
        return self.employee_set.filter(is_active=True).count()


class Employee(BaseModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, null=True)
    user = models.OneToOneField("accounts.User", on_delete=models.PROTECT, limit_choices_to={"is_active": True}, related_name="employee", null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    employee_id = models.CharField(max_length=128, unique=True, null=True)
    gender = models.CharField(max_length=128, choices=GENDER_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=128, choices=MARITAL_CHOICES, blank=True, null=True)
    personal_email = models.EmailField(max_length=128, null=True)
    mobile = models.CharField(max_length=128, null=True, blank=True)
    whatsapp = models.CharField(max_length=128, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    religion = models.CharField(max_length=128, choices=RELIGION_CHOICES, blank=True, null=True)
    experience = models.TextField(null=True, blank=True)
    qualifications = models.TextField(null=True, blank=True)
    photo = ThumbnailerImageField(blank=True, null=True, upload_to="employees/photos/")

    # Company Info
    official_email = models.EmailField(max_length=128, blank=True, null=True)
    department = models.ForeignKey("employees.Department", on_delete=models.PROTECT, limit_choices_to={"is_active": True}, null=True)
    designation = models.ForeignKey("employees.Designation", on_delete=models.PROTECT, limit_choices_to={"is_active": True}, null=True)
    course = models.ForeignKey("masters.Course", on_delete=models.PROTECT, limit_choices_to={"is_active": True}, blank=True, null=True)
    is_also_tele_caller = models.CharField(max_length=128, choices=[("Yes", "Yes"), ("No", "No")], default="No")

    status = models.CharField(max_length=120, choices=EMPLOYEE_STATUS_CHOICES, default='Appointed')
    employment_type = models.CharField(max_length=128, choices=EMPLOYMENT_TYPE_CHOICES, blank=True, null=True)
    resigned_date = models.DateField(null=True, blank=True)
    notice_date = models.DateField('Notice Period Last Date', null=True, blank=True)
    resigned_form = models.FileField(null=True, blank=True, upload_to="resigned-form/")
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.CharField(max_length=100, null=True, blank=True)

    # Parent Info
    father_name = models.CharField(max_length=128, blank=True, null=True)
    father_mobile = models.CharField(max_length=128, blank=True, null=True)
    mother_name = models.CharField(max_length=128, blank=True, null=True)
    guardian_name = models.CharField(max_length=128, blank=True, null=True)
    guardian_mobile = models.CharField(max_length=128, blank=True, null=True)
    relationship_with_employee = models.CharField("Guardian Relationship With Employee", max_length=128, blank=True, null=True)

    # Dates
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_confirmation = models.DateField(blank=True, null=True)

    # Job 
    aadhar = models.FileField(null=True, upload_to="employees/doc/aadhar/", blank=True)
    pancard = models.FileField(null=True, blank=True, upload_to="employees/doc/pancard/")
    signature = models.ImageField(
        upload_to="employees/doc/signature/",
        null=True,
        blank=True,
        help_text="Upload a transparent signature image (PNG recommended)"
    )   
    offer_letter = models.FileField(blank=True, null=True, upload_to="employees/doc/")
    joining_letter = models.FileField(blank=True, null=True, upload_to="employees/doc/")
    agreement_letter = models.FileField(blank=True, null=True, upload_to="employees/doc/")
    experience_letter = models.FileField(blank=True, null=True, upload_to="employees/doc/")

    # Residence Info
    type_of_residence = models.CharField(max_length=128, choices=RESIDENCE_CHOICES, blank=True, null=True)
    residence_name = models.CharField(max_length=128, blank=True, null=True)
    residential_address = models.TextField(blank=True, null=True)
    residence_contact = models.CharField(max_length=128, blank=True, null=True)
    residential_zip_code = models.CharField(max_length=128, blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    permanent_zip_code = models.CharField(max_length=128, blank=True, null=True)

    # Account Info
    bank_name = models.CharField(max_length=128, blank=True, null=True)
    account_name = models.CharField(max_length=128, blank=True, null=True)
    account_number = models.CharField("Bank Account Number", max_length=128, blank=True, null=True)
    ifsc_code = models.CharField("Bank IFSC Code", max_length=128, blank=True, null=True)
    bank_branch = models.CharField(max_length=128, blank=True, null=True)
    pan_number = models.CharField("PAN Card Number", max_length=128, blank=True, null=True)

    # Emergency Info
    blood_group = models.CharField(max_length=128, choices=BLOOD_CHOICES, blank=True, null=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Commission percentage (Per Admission)")
    hra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    transportation_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_appointment_letter_sent = models.BooleanField(default=False)
    appointment_letter_sent_at = models.DateTimeField(null=True, blank=True)
    account = models.OneToOneField('accounting.Account', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.branch}"
    
    @property
    def total_salary(self):
        return sum([
            self.basic_salary or Decimal("0.00"),
            self.hra or Decimal("0.00"),
            self.other_allowance or Decimal("0.00"),
            self.transportation_allowance or Decimal("0.00"),
        ])

    def fullname(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def get_absolute_url(self):
        return reverse_lazy("employees:employee_detail", kwargs={"pk": self.pk})

    def get_image_url(self):
        if self.photo: 
            return self.photo.url

        name = self.user.get_full_name() or self.user.username
        initials = name[:2].upper()
        return f"https://ui-avatars.com/api/?name={initials}&background=fdc010&color=fff&size=128"

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:employee_list")

    @staticmethod
    def get_create_url():
        return reverse_lazy("employees:employee_create")

    def get_update_url(self):
        return reverse_lazy("employees:employee_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("employees:employee_delete", kwargs={"pk": self.pk})

    def is_hod_staff(self):
        return Department.objects.filter(department_lead=self).exists()

    @property
    def leave_requests_count(self):
        return self.leave_requests.filter(is_active=True).count()


    @property
    def approved_count(self):
        return self.leave_requests.filter(status="approved", is_active=True).count()


    @property
    def pending_count(self):
        return self.leave_requests.filter(status="pending", is_active=True).count()


    @property
    def rejected_count(self):
        return self.leave_requests.filter(status="rejected", is_active=True).count()


    @property
    def active_leave_count(self):
        """
        Leaves currently running (today between start & end and approved)
        """
        today = timezone.now().date()
        return self.leave_requests.filter(
            is_active=True,
            status="approved",
            start_date__lte=today,
            end_date__gte=today,
        ).count()

    @property
    def leave_balance_obj(self):
        """Retrieves balance and handles month-to-month logic."""
        balance, created = EmployeeLeaveBalance.objects.get_or_create(employee=self)
        # Ensure we check accrual every time we look at the balance
        balance.accrue_monthly()
        return balance

    @property
    def total_balance_leaves(self):
        """The actual Total Available (Carry + Fresh)"""
        return self.leave_balance_obj.paid_leave_balance

    @property
    def total_balance_wfh(self):
        """The actual Total Available WFH (Carry + Fresh)"""
        return self.leave_balance_obj.wfh_balance

    # --- REPORTING PROPERTIES ---

    @property
    def actual_paid_carry_forward(self):
        """Returns the actual days brought over from last month."""
        return self.leave_balance_obj.paid_carry_forward

    @property
    def actual_wfh_carry_forward(self):
        return self.leave_balance_obj.wfh_carry_forward

    @property
    def current_month_paid_available(self):
        """Used in Template: Total Days available right now"""
        return self.total_balance_leaves
    
    @property
    def current_month_wfh_available(self):
        """Used in Template: Total WFH available right now"""
        return self.total_balance_wfh
    
    @property
    def current_month_fresh_paid(self):
        """Constant: 1.0"""
        return self.leave_balance_obj.MONTHLY_PAID
    
    @property
    def current_month_fresh_wfh(self):
        """Constant: 1.0"""
        return self.leave_balance_obj.MONTHLY_WFH
    
    # --- PROGRESS BARS ---
    
    @property
    def paid_cf_percent(self):
        """Percentage of Carry Limit used"""
        obj = self.leave_balance_obj
        # We compare actual carry vs the CARRY_LIMIT
        limit = obj.CARRY_LIMIT_PAID 
        if limit > 0:
            return min((self.actual_paid_carry_forward / limit) * 100, 100)
        return 0

    @property
    def wfh_cf_percent(self):
        obj = self.leave_balance_obj
        limit = obj.CARRY_LIMIT_WFH
        if limit > 0:
            return min((self.actual_wfh_carry_forward / limit) * 100, 100)
        return 0

    def save(self, *args, **kwargs):
        """Custom save to deactivate user if status != 'Appointed'"""
        # Rename photo file uniquely if new record with image
        if not self.pk and self.photo:
            self.photo.name = f"{uuid.uuid4()}{os.path.splitext(self.photo.name)[1]}"

        # If linked user exists and employee status is changed to not 'Appointed'
        if self.user:
            if self.status != 'Appointed':
                if self.user.is_active:
                    self.user.is_active = False
                    self.user.save(update_fields=['is_active'])
            else:
                # If reappointed, make sure user is active again
                if not self.user.is_active:
                    self.user.is_active = True
                    self.user.save(update_fields=['is_active'])

        super().save(*args, **kwargs)


class Payroll(BaseModel):
    payroll_year = models.CharField(
        max_length=180,
        choices=YEAR_CHOICES, # Ensure these choices are defined in your constants
        default=current_year
    )
    payroll_month = models.CharField(
        max_length=180,
        choices=MONTH_CHOICES, # Ensure these choices are defined
        default=current_month
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True}
    )
    
    # Salary Components
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    allowances_description = models.TextField(blank=True, null=True)
    
    # Leave and Absence Logic
    total_leaves = models.DecimalField(
        max_digits=5, decimal_places=1, default=0.0, 
        help_text="Total approved leaves taken this month (Paid + Unpaid)"
    )
    paid_leaves = models.DecimalField(
        max_digits=5, decimal_places=1, default=0.0, 
        help_text="Leaves covered by balance (Carry over + Current Month)"
    )
    absences = models.DecimalField(
        max_digits=5, decimal_places=1, default=0.0,
        verbose_name="Unpaid Absences",
        help_text="Excess leaves to deduct from salary"
    )
    
    # Other adjustments
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deductions_description = models.TextField(blank=True, null=True)
    overtime = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Totals
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=180, choices=PAYROLL_STATUS, default="Pending")

    transaction = models.OneToOneField(
        'transactions.Transaction', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='payroll_record'
    )

    class Meta:
        ordering = ("-payroll_year", "-payroll_month")
        verbose_name = "Payroll"
        verbose_name_plural = "Payrolls"
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "payroll_year", "payroll_month"],
                name="unique_employee_payroll"
            )
        ]

    def __str__(self):
        return f"{self.employee.fullname()} - {self.payroll_year}/{self.get_payroll_month_display()}"

    def clean(self):
        """Ensure net salary doesn't go below zero before saving."""
        if self.net_salary < 0:
            self.net_salary = 0

    def calculate_leaves_and_absences(self):
        """
        Calculates Total Leaves, Paid Leaves, and Unpaid Absences based on
        EmployeeLeaveBalance logic (Carry Limit + 1).
        """
        # 1. Get Balance Info
        balance, _ = EmployeeLeaveBalance.objects.get_or_create(employee=self.employee)
        
        # Calculate Limits for THIS month:
        # Limit = min(CarryForward, 6) + 1 (Current Month)
        max_paid_limit = min(balance.paid_carry_forward, balance.CARRY_LIMIT_PAID) + balance.MONTHLY_PAID
        max_wfh_limit = min(balance.wfh_carry_forward, balance.CARRY_LIMIT_WFH) + balance.MONTHLY_WFH

        # 2. Fetch Actual Taken Leaves for this Payroll Month
        leaves_qs = EmployeeLeaveRequest.objects.filter(
            employee=self.employee,
            status='approved',
            start_date__year=self.payroll_year,
            start_date__month=self.payroll_month
        )

        taken_paid_leaves = 0.0
        taken_wfh_leaves = 0.0

        for leave in leaves_qs:
            # Calculate days for this specific leave
            days = leave.total_days
            if leave.leave_type == 'wfh':
                taken_wfh_leaves += days
            else:
                taken_paid_leaves += days

        # 3. Calculate Unpaid Absences (Excess)
        # Absences = Taken - Limit. (If Taken < Limit, Absences is 0)
        unpaid_paid_type = max(0.0, taken_paid_leaves - max_paid_limit)
        unpaid_wfh_type = max(0.0, taken_wfh_leaves - max_wfh_limit)

        total_absences = unpaid_paid_type + unpaid_wfh_type
        
        # 4. Calculate Covered (Paid) Leaves
        # Total Taken - Unpaid = Paid
        total_taken = taken_paid_leaves + taken_wfh_leaves
        total_paid_leaves = total_taken - total_absences

        # 5. Set Values to Model
        self.total_leaves = Decimal(str(total_taken))
        self.paid_leaves = Decimal(str(total_paid_leaves))
        
        # Only overwrite absences if it's 0 (allows manual override by HR if needed)
        # Or you can force overwrite: self.absences = Decimal(str(total_absences))
        if self.absences == 0 and total_absences > 0:
            self.absences = Decimal(str(total_absences))

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # 1. Auto-Calculate Leaves if this is a new record or absences is 0
        # This ensures we pull data from the Leave System
        self.calculate_leaves_and_absences()

        # 2. Salary Calculation Logic
        working_days = Decimal("30.0")
        per_day_salary = self.basic_salary / working_days

        # Absence Amount calculation
        absence_amount = Decimal(self.absences) * per_day_salary

        # Gross = Basic + Allowances + Overtime
        self.gross_salary = self.basic_salary + self.allowances + self.overtime
        
        # Net = Gross - Deductions - Absence Amount
        self.net_salary = self.gross_salary - self.deductions - absence_amount
        
        # Ensure net salary is not negative
        if self.net_salary < 0:
            self.net_salary = 0

        super().save(*args, **kwargs)

        # 3. CREATE ACCOUNTING ENTRY
        if is_new and not self.transaction:
            self.create_accounting_entry()

    def create_accounting_entry(self):
        """
        Debit: Salary Expense Account
        Credit: Employee Ledger Account (Liability)
        """
        from transactions.models import Transaction, TransactionEntry
        from accounting.models import Account

        with db_transaction.atomic():
            # Determine Expense Account based on designation
            is_teacher = self.employee.designation and "Teacher" in self.employee.designation.name
            expense_code = '50001' if is_teacher else '50002'
            
            try:
                expense_account = Account.objects.get(code=expense_code, branch=self.employee.branch)
            except Account.DoesNotExist:
                expense_account = Account.objects.filter(under__code='STAFF_EXPENSES', branch=self.employee.branch).first()

            if not self.employee.account:
                return 

            # Create Transaction Header
            self.transaction = Transaction.objects.create(
                branch=self.employee.branch,
                transaction_type='payroll',
                status='posted',
                date=timezone.now(),
                voucher_number=f"PAY/VOUCH/{self.payroll_year}/{self.payroll_month}/{self.employee.pk}",
                narration=f"Monthly salary for {self.get_payroll_month_display()} {self.payroll_year} - {self.employee.fullname()}",
                invoice_amount=self.net_salary,
                total_amount=self.net_salary,
                balance_amount=self.net_salary
            )
            
            # Debit Salary Expense
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=expense_account,
                debit_amount=self.net_salary,
                credit_amount=0,
                description=f"Salary Expense - {self.employee.fullname()}"
            )
            
            # Credit Employee Ledger (Liability)
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=self.employee.account,
                debit_amount=0,
                credit_amount=self.net_salary,
                description="Salary Payable"
            )
            
            # Save the transaction link back to payroll
            Payroll.objects.filter(pk=self.pk).update(transaction=self.transaction)

    @property
    def total_paid(self):
        from employees.models import PayrollPayment 
        return PayrollPayment.objects.filter(payroll=self, is_active=True).aggregate(
            total=Sum("amount_paid")
        )["total"] or Decimal("0.00")

    @property
    def remaining_salary(self):
        return max(self.net_salary - self.total_paid, Decimal("0.00"))

    # Standard URLs
    def get_absolute_url(self):
        return reverse_lazy("employees:payroll_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:payroll_list")

    @staticmethod
    def get_create_url():
        return reverse_lazy("employees:payroll_create")

    def get_update_url(self):
        return reverse_lazy("employees:payroll_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("employees:payroll_delete", kwargs={"pk": self.pk})

    
class PayrollPayment(BaseModel):
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, limit_choices_to={"is_active": True})
    payroll = models.ForeignKey("employees.Payroll", on_delete=models.CASCADE, null=True, limit_choices_to={"is_active": True})
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    paid_from = models.ForeignKey(
        "accounting.Account", 
        on_delete=models.PROTECT, 
        related_name="payroll_payments",
        limit_choices_to={'under__code__in': ['BANK_ACCOUNT', 'CASH_ACCOUNT']},
        blank=True, null=True
    )
    transaction = models.OneToOneField(
        'transactions.Transaction', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )

    class Meta:
        ordering = ("-payment_date",)
        verbose_name = "Payroll Payment"
        verbose_name_plural = "Payroll Payments"

    def __str__(self):
        return f"Payment of {self.payment_date} towards {self.payment_date}"

    def create_accounting_entry(self):
        """
        Logic: 
        Debit: Employee Ledger (Reduces Liability/Payable)
        Credit: Bank/Cash Account (Asset goes down)
        """
        from transactions.models import Transaction, TransactionEntry

        # 1. PRE-FLIGHT VALIDATION: Prevent NOT NULL errors
        if not self.employee.account:
            return False, "Employee has no accounting ledger linked."
        if not self.paid_from:
            return False, "Please select the 'Paid From' account (Bank/Cash)."

        with db_transaction.atomic():
            # 2. Create or Update the Transaction Header
            if not self.transaction:
                new_trans = Transaction.objects.create(
                    branch=self.employee.branch,
                    transaction_type='payment',
                    status='posted',
                    date=timezone.now(),
                    voucher_number=f"PAY-SLIP/{self.pk}",
                    narration=f"Salary Payment for {self.payroll} via {self.paid_from.name}",
                    invoice_amount=self.amount_paid,
                    total_amount=self.amount_paid
                )
                # Link transaction using update() to bypass signals/recursion
                self.__class__.objects.filter(pk=self.pk).update(transaction=new_trans)
                self.transaction = new_trans
            else:
                self.transaction.invoice_amount = self.amount_paid
                self.transaction.total_amount = self.amount_paid
                self.transaction.save(update_fields=['invoice_amount', 'total_amount'])

            # 3. Re-create Entries
            self.transaction.entries.all().delete()

            # Entry 1: Debit Employee Account
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=self.employee.account,
                debit_amount=self.amount_paid,
                credit_amount=0,
                description=f"Salary Paid to {self.employee.fullname()}"
            )

            # Entry 2: Credit Cash/Bank Account
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=self.paid_from,
                debit_amount=0,
                credit_amount=self.amount_paid,
                description=f"Withdrawal for Employee Salary"
            )
            return True, "Success"

    def get_absolute_url(self):
        return reverse_lazy("employees:payroll_payment_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:payroll_payment_list")

    @staticmethod
    def get_create_url():
        return reverse_lazy("employees:payroll_payment_create")

    def get_update_url(self):
        return reverse_lazy("employees:payroll_payment_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("employees:payroll_payment_delete", kwargs={"pk": self.pk})

    
class AdvancePayrollPayment(BaseModel):
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True}
    )
    payroll = models.ForeignKey("employees.Payroll", on_delete=models.CASCADE, null=True, limit_choices_to={"is_active": True})
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    paid_from = models.ForeignKey(
        "accounting.Account", 
        on_delete=models.PROTECT, 
        related_name="advance_payroll_payments",
        limit_choices_to={'under__code__in': ['BANK_ACCOUNT', 'CASH_ACCOUNT']},
        blank=True, null=True
    )
    transaction = models.OneToOneField(
        'transactions.Transaction', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )

    class Meta:
        ordering = ("-payment_date",)
        verbose_name = "Advance Payroll Payment"
        verbose_name_plural = "Advance Payroll Payments"

    def __str__(self):
        return f"Advance {self.amount_paid} - {self.employee} - {self.payroll} - ({self.payment_date})"

    def create_accounting_entry(self):
        """
        Logic:
        Debit: Employee Account (As an Advance/Receivable)
        Credit: Bank/Cash Account
        """
        from transactions.models import Transaction, TransactionEntry

        if not self.employee.account:
            return False, "Employee has no accounting ledger linked."
        if not self.paid_from:
            return False, "Please select the 'Paid From' account."

        with db_transaction.atomic():
            if not self.transaction:
                new_trans = Transaction.objects.create(
                    branch=self.employee.branch,
                    transaction_type='payment',
                    status='posted',
                    date=timezone.now(),
                    voucher_number=f"ADV-PAY/{self.pk}",
                    narration=f"Advance Salary to {self.employee.fullname()}",
                    invoice_amount=self.amount_paid,
                    total_amount=self.amount_paid
                )
                self.__class__.objects.filter(pk=self.pk).update(transaction=new_trans)
                self.transaction = new_trans
            else:
                self.transaction.invoice_amount = self.amount_paid
                self.transaction.total_amount = self.amount_paid
                self.transaction.save()

            self.transaction.entries.all().delete()

            # Debit Employee Account (Advance)
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=self.employee.account,
                debit_amount=self.amount_paid,
                credit_amount=0,
                description=f"Salary Advance to {self.employee.fullname()}"
            )

            # Credit Cash/Bank
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=self.paid_from,
                debit_amount=0,
                credit_amount=self.amount_paid,
                description=f"Advance Payment Withdrawal"
            )
            return True, "Success"

    def get_absolute_url(self):
        return reverse_lazy("employees:advance_payroll_payment_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:advance_payroll_payment_list")

    @staticmethod
    def get_create_url():
        return reverse_lazy("employees:advance_payroll_payment_create")

    def get_update_url(self):
        return reverse_lazy("employees:advance_payroll_payment_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("employees:advance_payroll_payment_delete", kwargs={"pk": self.pk})
    

class Partner(BaseModel):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.PROTECT,
        limit_choices_to={"is_active": True},
        related_name="partner",
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=128)
    photo = ThumbnailerImageField(
        blank=True,
        null=True,
        upload_to="partners/photos/"
    )
    partner_id = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True
    )
    contact_number = models.CharField(
        max_length=128,
        blank=True,
        null=True
    )
    whatsapp_number = models.CharField(
        max_length=128,
        blank=True,
        null=True
    )
    email = models.EmailField(max_length=128)
    address = models.TextField(blank=True, null=True)

    shares_owned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Number of shares owned by the partner"
    )

    def __str__(self):
        return self.full_name

    # -----------------------------
    # Share Calculations
    # -----------------------------

    @property
    def share_percentage(self):
        """
        Partner's share percentage based on total company shares
        """
        company = CompanyProfile.objects.first()
        if not company or company.number_of_shares == 0:
            return Decimal("0.00")

        return round(
            (self.shares_owned / Decimal(company.number_of_shares)) * 100,
            2
        )

    @property
    def share_amount(self):
        """
        Partner's share value based on company total value
        """
        company = CompanyProfile.objects.first()
        if not company:
            return Decimal("0.00")

        percentage = self.share_percentage / Decimal("100")
        return round(company.total_value * percentage, 2)

    @property
    def available_shares(self):
        """
        Remaining shares available for allocation
        """
        company = CompanyProfile.objects.first()
        if not company:
            return Decimal("0.00")

        partners_total = Partner.objects.aggregate(
            total=models.Sum("shares_owned")
        )["total"] or Decimal("0.00")

        return (
            Decimal(company.number_of_shares)
            - Decimal(company.company_hold_shares)
            - partners_total
        )

    # -----------------------------
    # Validation
    # -----------------------------

    def clean(self):
        company = CompanyProfile.objects.first()
        if not company:
            raise ValidationError("Company profile is not configured.")

        partners_total = Partner.objects.exclude(pk=self.pk).aggregate(
            total=models.Sum("shares_owned")
        )["total"] or Decimal("0.00")

        remaining = (
            Decimal(company.number_of_shares)
            - Decimal(company.company_hold_shares)
            - partners_total
        )

        if self.shares_owned > remaining:
            raise ValidationError({
                "shares_owned": (
                    f"Only {remaining} shares are available. "
                    f"You cannot assign {self.shares_owned} shares."
                )
            })

    # -----------------------------
    # URLs
    # -----------------------------

    def get_absolute_url(self):
        return reverse_lazy(
            "employees:partner_detail",
            kwargs={"pk": self.pk}
        )

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:partner_list")

    @staticmethod
    def get_create_url():
        return reverse_lazy("employees:partner_create")

    def get_update_url(self):
        return reverse_lazy(
            "employees:partner_update",
            kwargs={"pk": self.pk}
        )

    def get_delete_url(self):
        return reverse_lazy(
            "employees:partner_delete",
            kwargs={"pk": self.pk}
        )

    
class EmployeeLeaveRequest(BaseModel):
    LEAVE_TYPE_CHOICES = (
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('emergency', 'Emergency Leave'),
        ('wfh', 'Work From Home'), 
    )

    DAY_TYPE_CHOICES = (
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
    )

    SESSION_CHOICES = (
        ('first_half', 'First Half (Morning)'),
        ('second_half', 'Second Half (Afternoon)'),
    )

    LEAVE_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    employee = models.ForeignKey(
        "employees.Employee", 
        on_delete=models.CASCADE, 
        related_name="leave_requests"
    )
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE_CHOICES, default='casual')
    
    leave_day_type = models.CharField(
        max_length=20, 
        choices=DAY_TYPE_CHOICES, 
        default='full_day'
    )
    half_day_session = models.CharField(
        max_length=20, 
        choices=SESSION_CHOICES, 
        blank=True, 
        null=True
    )
    
    subject = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    attachment = models.FileField(upload_to="employee_leave_attachments/", blank=True, null=True)
    
    status = models.CharField(
        max_length=30,
        choices=LEAVE_STATUS_CHOICES, 
        default="pending"
    )
    
    approved_by = models.ForeignKey(
        "employees.Employee", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="approved_employee_leaves",
        verbose_name="Approved By"
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True, help_text="Approval or Rejection remarks")
    
    # Flag to track if balance has been deducted to prevent double deduction
    is_balance_deducted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Employee Leave Request'
        verbose_name_plural = 'Employee Leave Requests'

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date})"

    @property
    def total_days(self):
        if self.leave_day_type == 'half_day':
            return 0.5
        return (self.end_date - self.start_date).days + 1

    def save(self, *args, **kwargs):
        # Let the signal handle balance deduction to avoid duplication
        super().save(*args, **kwargs)

    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:employee_leave_request_list")
    
    def get_absolute_url(self):
        return reverse_lazy("employees:employee_leave_request_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("employees:employee_leave_request_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("employees:employee_leave_request_delete", kwargs={"pk": self.pk})

    
class EmployeeLeaveBalance(BaseModel):
    employee = models.OneToOneField(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="leave_balance"
    )

    # 1. Defaults set to 1.0 (New employees start with 1 day immediately)
    paid_leave_balance = models.FloatField(default=1.0)
    wfh_balance = models.FloatField(default=1.0)

    # 2. History Snapshots (For the Report Page)
    paid_carry_forward = models.FloatField(default=0.0)
    wfh_carry_forward = models.FloatField(default=0.0)

    last_accrual_month = models.DateField(default=date.today)

    # --- CONSTANTS ---
    # CARRY_LIMIT: The maximum days allowed to travel to the next month.
    # MONTHLY: The fresh days added every month.
    CARRY_LIMIT_PAID = 6.0 
    CARRY_LIMIT_WFH = 6.0
    
    MONTHLY_PAID = 1.0
    MONTHLY_WFH = 1.0

    def accrue_monthly(self):
        """
        Equation: NewBalance = min(OldBalance, CarryLimit) + MonthlyAccrual
        Result: If Limit is 6 and Monthly is 1, max available becomes 7.
        """
        today = date.today()
        last_check = self.last_accrual_month
        
        # Calculate months passed
        months_passed = (today.year - last_check.year) * 12 + (today.month - last_check.month)

        if months_passed > 0:
            # --- PAID LEAVE ---
            # 1. Cap the old balance at the Carry Limit (e.g., max 6)
            actual_carry_paid = min(self.paid_leave_balance, self.CARRY_LIMIT_PAID)
            
            # 2. Update the snapshot for the report
            self.paid_carry_forward = actual_carry_paid
            
            # 3. Add fresh leaves on top of the capped carry over
            self.paid_leave_balance = actual_carry_paid + (months_passed * self.MONTHLY_PAID)


            # --- WFH LEAVE ---
            # 1. Cap old balance
            actual_carry_wfh = min(self.wfh_balance, self.CARRY_LIMIT_WFH)
            
            # 2. Update snapshot
            self.wfh_carry_forward = actual_carry_wfh
            
            # 3. Add fresh leaves
            self.wfh_balance = actual_carry_wfh + (months_passed * self.MONTHLY_WFH)

            # Update date to the 1st of current month
            self.last_accrual_month = today.replace(day=1)
            self.save()

    def __str__(self):
        return f"{self.employee} - Paid: {self.paid_leave_balance}, WFH: {self.wfh_balance}"

    
class EmployeeAttendanceRegister(BaseModel):
    employee = models.ForeignKey(
        "employees.Employee", 
        on_delete=models.CASCADE, 
        related_name="attendance_register"
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[('present', 'Present'), ('absent', 'Absent')], default='present')

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"

    class Meta:
        ordering = ['-created']
        unique_together = ('employee', 'date')
        verbose_name = 'Employee Attendance Register'
        verbose_name_plural = 'Employee Attendance Registers'


    @staticmethod
    def get_list_url():
        return reverse_lazy("employees:employee_attendance_list")
    
    def get_absolute_url(self):
        return reverse_lazy("employees:employee_attendance_detail", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse_lazy("employees:employee_attendance_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("employees:employee_attendance_delete", kwargs={"pk": self.pk})
