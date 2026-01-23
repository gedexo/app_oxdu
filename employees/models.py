import datetime
from django.utils import timezone
import calendar
import os
import uuid
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
    hra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    transportation_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_appointment_letter_sent = models.BooleanField(default=False)
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
        choices=YEAR_CHOICES,
        default=current_year
    )
    payroll_month = models.CharField(
        max_length=180,
        choices=MONTH_CHOICES,
        default=current_month
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True}
    )
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    allowances_description = models.TextField(blank=True, null=True)
    absences = models.DecimalField(max_digits=30, decimal_places=1, default=0.0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deductions_description = models.TextField(blank=True, null=True)
    overtime = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=180, choices=PAYROLL_STATUS, default="Pending")

    transaction = models.OneToOneField(
        'transactions.Transaction', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='payroll_record'
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # -------------------------
        # Salary Calculation
        # -------------------------
        working_days = 30
        per_day_salary = self.basic_salary / working_days

        if self.employee.employment_type == "PROBATION":
            unpaid_absence_days = self.absences
        else:
            unpaid_absence_days = max(0, self.absences - 1)

        absence_amount = unpaid_absence_days * per_day_salary

        self.gross_salary = self.basic_salary + self.allowances + self.overtime
        self.net_salary = self.gross_salary - self.deductions - absence_amount

        super().save(*args, **kwargs)

        # -------------------------
        # CREATE ACCOUNTING ENTRY
        # -------------------------
        # Create transaction immediately on payroll creation
        if is_new and not self.transaction:
            self.create_accounting_entry()

    def create_accounting_entry(self):
        """
        Logic: 
        Debit: Salary Expense Account (Teaching/Non-Teaching)
        Credit: Employee Ledger Account (Liability)
        """
        from transactions.models import Transaction, TransactionEntry
        from accounting.models import Account
        from accounting.constants import ACCOUNT_CODE_MAPPING

        with db_transaction.atomic():
            # 1. Determine Expense Account based on Employee designation/type
            # You might want to map this more dynamically
            expense_code = '50001' if self.employee.designation and "Teacher" in self.employee.designation.name else '50002'
            try:
                expense_account = Account.objects.get(code=expense_code, branch=self.employee.branch)
            except Account.DoesNotExist:
                # Fallback to a general staff expense if specific not found
                expense_account = Account.objects.filter(under__code='STAFF_EXPENSES', branch=self.employee.branch).first()

            if not self.employee.account:
                raise ValidationError(f"Employee {self.employee.fullname()} has no linked accounting ledger.")

            # 2. Create Transaction Header
            if not self.transaction:
                self.transaction = Transaction.objects.create(
                    branch=self.employee.branch,
                    transaction_type='payroll',
                    status='posted',
                    date=timezone.now(),
                    voucher_number=f"PAYROLL/{self.payroll_year}/{self.payroll_month}/{self.employee.pk}",
                    narration=f"Salary provision for {self.payroll_month}/{self.payroll_year} - {self.employee.fullname()}",
                    invoice_amount=self.net_salary,
                    total_amount=self.net_salary,
                    balance_amount=self.net_salary
                )
            
            # 3. Create Entries (Double Entry)
            self.transaction.entries.all().delete() # Refresh entries
            
            # Debit Salary Expense
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=expense_account,
                debit_amount=self.net_salary,
                credit_amount=0,
                description="Salary Expense"
            )
            
            # Credit Employee Ledger (Liability created)
            TransactionEntry.objects.create(
                transaction=self.transaction,
                account=self.employee.account,
                debit_amount=0,
                credit_amount=self.net_salary,
                description="Salary Payable"
            )
            
            self.save(update_fields=['transaction'])

    @property
    def total_paid(self):
        return PayrollPayment.objects.filter(payroll=self, is_active=True).aggregate(
            total=models.Sum("amount_paid")
        )["total"] or 0

    @property
    def remaining_salary(self):
        advance_total = AdvancePayrollPayment.objects.filter(
            payroll=self, is_active=True
        ).aggregate(total=models.Sum("amount_paid"))["total"] or 0
        return max(self.net_salary - self.total_paid - advance_total, 0)

    class Meta:
        ordering = ("-payroll_month",)
        verbose_name = "Payroll"
        verbose_name_plural = "Payrolls"
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "payroll_year", "payroll_month"],
                name="unique_employee_payroll"
            )
        ]

    def __str__(self):
        return f"{self.employee} - {self.payroll_year} - {self.get_payroll_month_display()}"

    @property
    def display_title(self):
        return f"{DateFormat(self.date).format('Y F')} - ({self.employee.first_name})"

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

    # ✅ Decimal shares (allows 1.25, 0.5, etc.)
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
    employee = models.ForeignKey(
        "employees.Employee", 
        on_delete=models.CASCADE, 
        related_name="leave_requests"
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

    class Meta:
        ordering = ['-created']
        verbose_name = 'Employee Leave Request'
        verbose_name_plural = 'Employee Leave Requests'

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date})"

    @property
    def total_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:employee_leave_request_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:employee_leave_request_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:employee_leave_request_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:employee_leave_request_delete", kwargs={"pk": self.pk})