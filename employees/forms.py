from core.base import BaseForm
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Sum

from .models import Department, Partner
from .models import Designation
from .models import Employee, Payroll, PayrollPayment, AdvancePayrollPayment
from masters.models import Course
from django import forms


class DepartmentForm(BaseForm):
    class Meta:
        model = Department
        fields = "__all__"


class DesignationForm(BaseForm):
    class Meta:
        model = Designation
        fields = "__all__"
        
    
class CourseForm(BaseForm):
    class Meta:
        model = Course
        fields = "__all__"


class EmployeeForm(BaseForm):
    class Meta:
        model = Employee
        exclude = ("user", "status", "resigned_date", "notice_date", "resigned_form", "termination_date", "termination_reason")


class EmployeePhotoForm(BaseForm):
    class Meta:
        model = Employee
        fields = ['photo']
        widgets = {'photo': forms.FileInput(attrs={'class': 'form-control d-none'})}


class EmployeePersonalDataForm(BaseForm):
    class Meta:
        model = Employee
        fields = (
            "is_active",
            "first_name",
            "last_name",
            "personal_email",
            "gender",
            "marital_status",
            "mobile",
            "whatsapp",
            "date_of_birth",
            "religion",
            "blood_group",
            "experience",
            "qualifications",
            "photo",
        )

    def __init__(self, *args, **kwargs):
        # Pop the request out of kwargs if passed
        request = kwargs.pop('request', None)
        super(EmployeePersonalDataForm, self).__init__(*args, **kwargs)

        self.fields['experience'].widget.attrs['rows'] = 3
        self.fields['qualifications'].widget.attrs['rows'] = 3

        if request and getattr(request.user, 'usertype', None) != "hr":
            self.fields['mobile'].required = True
            self.fields['whatsapp'].required = True
            self.fields['date_of_birth'].required = True


class EmployeeParentDataForm(BaseForm):
    class Meta:
        model = Employee
        fields = ("is_active", "father_name", "father_mobile", "mother_name", "guardian_name", "guardian_mobile", "relationship_with_employee")


class EmployeeAddressDataForm(BaseForm):
    class Meta:
        model = Employee
        fields = ("is_active", "type_of_residence", "residence_name", "residential_address", "residence_contact", "residential_zip_code", "permanent_address", "permanent_zip_code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['residential_address'].widget.attrs['rows'] = 3
        self.fields['permanent_address'].widget.attrs['rows'] = 3


class EmployeeOfficialDataForm(BaseForm):
    class Meta:
        model = Employee
        fields = (
            "is_active",
            "branch",
            "employee_id",
            "department",
            "designation",
            "course",
            "is_also_tele_caller",
            "date_of_confirmation",
            "date_of_joining",
            "official_email",
            "status",
            "employment_type",
            "resigned_date",
            "notice_date",
            "resigned_form",
            "termination_date",
            "termination_reason",
            "aadhar",
            "pancard",
            "offer_letter",
            "joining_letter",
            "agreement_letter",
            "experience_letter",
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(EmployeeOfficialDataForm, self).__init__(*args, **kwargs)

        if request and getattr(request.user, 'usertype', None) != "hr":
            self.fields['aadhar'].required = True


class EmployeeFinancialDataForm(BaseForm):
    class Meta:
        model = Employee
        fields = ("is_active", "bank_name", "account_name", "bank_branch", "account_number", "ifsc_code", "pan_number", "basic_salary", "hra", "transportation_allowance", "other_allowance")


class EmployeeDocumentsForm(BaseForm):
    class Meta:
        model = Employee
        fields = ["aadhar", "pancard"]

        def save(self, commit=True):
            instance = super().save(commit=False)
            if not self.cleaned_data.get('aadhar'):
                instance.aadhar = self.instance.aadhar
            if not self.cleaned_data.get('pancard'):
                instance.pancard = self.instance.pancard
            if commit:
                instance.save()
            return instance


class PayrollForm(BaseForm):
    class Meta:
        model = Payroll
        fields = ("payroll_year", "payroll_month", "employee", "basic_salary", "allowances", "allowances_description", "deductions", "deductions_description", "overtime", "absences")

    

class PayrollPaymentForm(forms.ModelForm):
    class Meta:
        model = PayrollPayment
        fields = (
            "employee",
            "payroll",
            "payment_date",
            "amount_paid",
            "payment_method",
            "reference_number",
            "remarks",
        )
        widgets = {
            'employee': forms.Select(attrs={'class': 'select2 form-select'}),
            'payroll': forms.Select(attrs={'class': 'select2 form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payroll = cleaned_data.get("payroll")
        amount_paid = cleaned_data.get("amount_paid")

        if payroll and amount_paid is not None:
            # Use the remaining_salary property from Payroll model
            remaining = payroll.remaining_salary

            if amount_paid > remaining:
                raise ValidationError({
                    "amount_paid": f"Amount cannot exceed pending salary ({remaining})"
                })

        return cleaned_data

    
class AdvancePayrollPaymentForm(forms.ModelForm):
    class Meta:
        model = AdvancePayrollPayment
        fields = (
            "employee",
            "payroll",
            "payment_date",
            "amount_paid",
            "payment_method",
            "reference_number",
            "remarks",
        )
        widgets = {
            'employee': forms.Select(attrs={'class': 'select2 form-select'}),
            'payroll': forms.Select(attrs={'class': 'select2 form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payroll = cleaned_data.get("payroll")
        amount_paid = cleaned_data.get("amount_paid")

        if payroll and amount_paid is not None:
            # Calculate 75% of basic salary
            max_advance = payroll.basic_salary * Decimal("0.75")

            # Already paid advances
            total_advance_paid = AdvancePayrollPayment.objects.filter(
                payroll=payroll, is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None).aggregate(
                total=Sum("amount_paid")
            )["total"] or Decimal("0.00")

            remaining_advance = max_advance - total_advance_paid

            if amount_paid > remaining_advance:
                raise ValidationError({
                    "amount_paid": f"Amount cannot exceed remaining advance limit ({remaining_advance})"
                })

        return cleaned_data
    

class PartnerForm(BaseForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter password",
                "autocomplete": "new-password",
            }
        ),
        label="Password",
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm password",
                "autocomplete": "new-password",  
            }
        ),
        label="Confirm Password",
        required=True
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter email address",
                "autocomplete": "off", 
            }
        ),
        label="Email",
        required=True
    )

    class Meta:
        model = Partner
        fields = (
            "full_name",
            "shares_owned",
            "contact_number",
            "whatsapp_number",
            "address",
            "photo",
            "email",
            "password",
            "confirm_password",
        )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data