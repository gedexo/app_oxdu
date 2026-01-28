from core.base import BaseForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from masters.models import Batch
from accounts.models import User
from .models import Admission, Attendance, FeeReceipt, FeeStructure, AdmissionEnquiry, AttendanceRegister, PaymentMethod
from django import forms
from decimal import Decimal
from branches.models import Branch
from employees.models import Employee


class AdmissionForm(BaseForm):
    class Meta:
        model = Admission
        exclude = ("user", "branch",)


class AdmissionPhotoForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ['photo']
        widgets = {'photo': forms.FileInput(attrs={'class': 'form-control d-none'})}


class AdmissionPersonalDataForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = (
            "is_active",
            "first_name",
            "last_name",
            "personal_email",
            "gender",
            "contact_number",
            "whatsapp_number",
            "date_of_birth",
            "religion",
            "marital_status",
            "blood_group",
            "qualifications",
            "course_mode",
            "photo",
        )

    def __init__(self, *args, **kwargs):
        super(AdmissionPersonalDataForm, self).__init__(*args, **kwargs)
        self.fields['qualifications'].widget.attrs['rows'] = 3

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo:
            max_size_kb = 100
            if photo.size > max_size_kb * 1024:
                raise ValidationError(f"Photo file size must be under {max_size_kb}KB.")
        return photo


class AdmissionParentDataForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ("is_active", "parent_first_name", "parent_last_name", "parent_contact_number", "parent_whatsapp_number", "parent_mail_id",)


class AdmissionAddressDataForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ("is_active", "home_address", "city", "district", "state", "pin_code",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['home_address'].widget.attrs['rows'] = 3


class AdmissionOfficialDataForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = (
            "is_active",
            "joining_date",
            "admission_date",
            "course_start_date",
            "branch",
            "course",
            "batch",
            "batch_type",
            "other_details",
            "care_of",
            "document",
            "signature",
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset = Batch.objects.none()

        self.fields['care_of'].queryset = User.objects.filter(is_active=True, is_superuser=False)

        self.fields['care_of'].label_from_instance = lambda obj: (
            f"{obj.first_name} {obj.last_name} - {obj.get_usertype_display()}".strip()
            if hasattr(obj, "get_usertype_display")
            else f"{obj.first_name} {obj.last_name}".strip()
        ) or obj.username

        course_id = None
        branch_id = None

        # 1) If instance has values, use them
        if self.instance:
            course_id = getattr(self.instance, "course_id", None)
            branch_id = getattr(self.instance, "branch_id", None)

        # 2) If POST data has values, override
        if "course" in self.data:
            course_id = self.data.get("course")
        if "branch" in self.data or "branch_id" in self.data:
            branch_id = self.data.get("branch") or self.data.get("branch_id")

        # 3) Build queryset if both IDs available
        if course_id and branch_id:
            try:
                self.fields['batch'].queryset = Batch.objects.filter(
                    course_id=course_id,
                    branch_id=branch_id
                )
            except Exception as e:
                print("Error building queryset:", e)


class AdmissionFinancialDataForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = (
            "fee_type",
            "installment_type",
            "custom_installment_months",
            "discount_amount",
            "admission_fee_amount",
            "admission_fee_payment_type",
        )
        widgets = {
            'fee_type': forms.Select(attrs={'class': 'select form-control', 'id': 'id_fee_type'}),
            'installment_type': forms.Select(attrs={'class': 'select form-control', 'id': 'id_installment_type'}),
            'custom_installment_months': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_custom_installment_months', 'min': '1'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'id': 'discount_amount'}),
            'admission_fee_amount': forms.NumberInput(attrs={'class': 'form-control', 'id': 'admission_fee_amount'}),
            'admission_fee_payment_type': forms.Select(attrs={'class': 'select form-control', 'id': 'id_admission_fee_payment_type'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        admission_fee_amount = cleaned_data.get("admission_fee_amount") or 0
        admission_fee_payment_type = cleaned_data.get("admission_fee_payment_type")
        fee_type = cleaned_data.get("fee_type")
        installment_type = cleaned_data.get("installment_type")
        custom_months = cleaned_data.get("custom_installment_months")

        if admission_fee_amount > 0 and not admission_fee_payment_type:
            self.add_error("admission_fee_payment_type", "This field is required when admission fee amount is greater than 0.")

        if fee_type == "installment" and installment_type == "custom":
            if not custom_months or custom_months < 1:
                self.add_error("custom_installment_months", "Please specify the number of months for the custom installment.")

        return cleaned_data

    def save(self, commit=True):
        admission = super().save(commit=False)
        if commit:
            admission.save()
        return admission
        

class AttendanceForm(BaseForm):
    student_name = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))
    student_pk = forms.IntegerField(widget=forms.HiddenInput())  

    class Meta:
        model = Attendance
        fields = ('status',)  
        widgets = {
            'status': forms.Select(attrs={'class': 'select form-control', 'required': True}),
        }


class AttendanceUpdateForm(forms.ModelForm):

    class Meta:
        model = Attendance
        fields = ('status','student' )  
        widgets = {
            'status': forms.Select(attrs={'class': 'select form-control', 'required': True}),
            'student': forms.Select(attrs={'class': 'select form-control', 'required': True}),
        }


class StudentFeeOverviewForm(forms.ModelForm):
    
    class Meta:
        model = Admission
        fields = ("first_name", "admission_number", "course", )
    

class RegistrationForm(forms.ModelForm):
    # password = forms.CharField(
    #     widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}),
    #     label="Password"
    # )
    
    class Meta:
        model = Admission
        fields = (
            "first_name", "last_name", "home_address", "contact_number", 
            "whatsapp_number", "joining_date", "date_of_birth", "city", "district", "state",
            "pin_code", "gender", "religion", "blood_group", "personal_email",
            "parent_first_name", "parent_last_name", "parent_contact_number",
            "parent_whatsapp_number", "parent_mail_id", "photo", "branch", "course",
            "batch", "qualifications", "document", "signature","passout_year", "cgpa_or_percentage",
            "parent_signature",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter First Name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Last Name"}),
            "home_address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter Home Address"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Contact Number"}),
            "whatsapp_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter WhatsApp Number"}),
            "joining_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter City"}),
            "district": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter District"}),
            "state": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter State"}),
            "pin_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Pin Code"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "religion": forms.Select(attrs={"class": "form-control"}),
            "blood_group": forms.Select(attrs={"class": "form-control"}),
            "personal_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter Email"}),
            "parent_first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Parent's First Name"}),
            "parent_last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Parent's Last Name"}),
            "parent_contact_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Parent's Contact Number"}),
            "parent_whatsapp_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Parent's WhatsApp Number"}),
            "parent_mail_id": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter Parent's Email"}),
            "photo": forms.FileInput(attrs={"class": "form-control-file"}),
            "branch": forms.Select(attrs={"class": "form-control"}),
            "course": forms.Select(attrs={"class": "form-control"}),
            "batch": forms.Select(attrs={"class": "form-control"}),
            "qualifications": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Education Qualification"}),
            "document": forms.FileInput(attrs={"class": "form-control form-control-file"}),
            "signature": forms.FileInput(attrs={"class": "form-control form-control-file"}),
            "passout_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter Passout Year"}),
            "cgpa_or_percentage": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter CGPA / Percentage"}),
            "parent_signature": forms.FileInput(attrs={"class": "form-control form-control-file"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['joining_date'].input_formats = ['%Y-%m-%d']
        self.fields['date_of_birth'].input_formats = ['%Y-%m-%d']

        required_fields = [
            "first_name", "last_name", "home_address", "contact_number",
            "whatsapp_number", "joining_date", "date_of_birth", "city", "district",
            "state", "pin_code", "gender", "religion", "blood_group", "personal_email",
            "parent_first_name", "parent_last_name", "parent_contact_number",
            "parent_whatsapp_number", "parent_mail_id", "photo", "branch", "course",
            "batch", "qualifications", "document", "signature", "passout_year",
            "cgpa_or_percentage","parent_signature",
        ]
        for field in required_fields:
            self.fields[field].required = True

        

class AdmissionEnquiryForm(forms.ModelForm):
    class Meta:
        model = AdmissionEnquiry
        fields = '__all__'

    
class AdmissionEnquiryUpdateForm(forms.ModelForm):
    class Meta:
        model = AdmissionEnquiry
        fields = ('full_name', 'city', 'branch', 'course', 'status', 'next_enquiry_date', 'remark', 'district', 'state',)
        

class AttendanceRegisterForm(forms.ModelForm):
    starting_time = forms.TimeField(required=False, disabled=True)
    ending_time = forms.TimeField(required=False, disabled=True)

    class Meta:
        model = AttendanceRegister
        exclude = ('branch', 'batch')
        fields = ('date', 'course', 'starting_time', 'ending_time')

    def __init__(self, *args, batch=None, **kwargs):
        super().__init__(*args, **kwargs)
        if batch:
            self.fields['starting_time'].initial = batch.starting_time
            self.fields['ending_time'].initial = batch.ending_time

    
class FeeReceiptForm(forms.ModelForm):
    class Meta:
        model = FeeReceipt
        fields = ("student", "date", "note",)

PaymentMethodFormSet = forms.inlineformset_factory(
    FeeReceipt,
    PaymentMethod,
    fields=("payment_type", "amount", "note"),
    extra=0,
    can_delete=True,
)


# Define the inline formset
FeeReceiptFormSet = forms.inlineformset_factory(
    Admission, 
    FeeReceipt,  
    form=FeeReceiptForm,
    can_delete=True  
)