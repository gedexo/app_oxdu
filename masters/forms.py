from datetime import datetime
from core.base import BaseForm
from django.forms import BaseModelFormSet, ValidationError, modelformset_factory
from tinymce.widgets import TinyMCE
from django import forms
from django.forms import inlineformset_factory
from tinymce.widgets import TinyMCE 
from django.contrib.auth import get_user_model
from core.choices import USERTYPE_CHOICES, CHOICES
from masters.models import RequestSubmission

User = get_user_model()

from .models import Activity, BranchActivity, ComplaintRegistration, Course, Feedback, FeedbackAnswer, FeedbackQuestion, Holiday, LeaveRequest, PDFBookResource, PdfBook, ChatSession, PlacementHistory, PublicMessage, Update, PlacementRequest, Batch, SyllabusMaster, Syllabus, Event, State, Tax


class PdfBookForm(forms.ModelForm):
    class Meta:
        model = PdfBook
        fields = ('name', "pdf")
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'pdf': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
        }
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['DELETE'] = forms.BooleanField(required=False)


PdfBookFormSet = inlineformset_factory(
    PDFBookResource,
    PdfBook,
    form=PdfBookForm,
    extra=1,
    can_delete=True,  
)

class CourseSelectionForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.filter(is_active=True))
    

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = ComplaintRegistration
        fields = ['complaint_type', 'complaint', 'status']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # get the logged-in user
        super().__init__(*args, **kwargs)

        # Only privileged users or super admin can see 'status'
        privileged_users = ["admin_staff", "ceo", "cfo", "coo", "hr", "cmo"]
        if user.usertype not in privileged_users and not user.is_superuser:
            self.fields.pop('status')


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatSession
        fields = ['message']


class UpdateForm(forms.ModelForm):
    class Meta:
        model = Update
        fields = ["title", "description", "image"]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter update title"
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control-file"
            }),
        }

    
class PlacementRequestForm(forms.ModelForm):
    class Meta:
        model = PlacementRequest
        fields = [
            "student",
            "resume",
            "portfolio_link",
            "behance_link",
            "experience",
            "status",  
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["student"].disabled = True

        if user and user.usertype == "student":
            self.fields.pop("status", None)

        elif user and user.usertype == "mentor":
            self.fields["resume"].required = False
            self.fields["student"].disabled = False

    
class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = [ "course", "batch_name", "description", "starting_time", "ending_time", "starting_date", "ending_date", "is_active",]

    
class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'description']


class BranchActivityForm(BaseForm):
    class Meta:
        model = BranchActivity
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        branch = cleaned_data.get("branch")
        activity = cleaned_data.get("activity")
        point = cleaned_data.get("point")
        month = cleaned_data.get("month")

        if self.instance and self.instance.pk:
            return cleaned_data  

        if branch and activity:
            if BranchActivity.objects.filter(branch=branch, activity=activity, month=month).exists():
                raise forms.ValidationError(
                    f"The branch '{branch}' already has the activity '{activity}' assigned."
                )

        if branch and point is not None:
            if BranchActivity.objects.filter(branch=branch, activity=activity, month=month, point=point).exists():
                raise forms.ValidationError(
                    f"The branch '{branch}' already has an activity with {point} points."
                )

        return cleaned_data
    

REQUEST_STATUS_CHOICES = (
    ("re_assign", "Re Assign"), ("approved", "Completed"), ("rejected", "Rejected"),
)

class RequestStatusUpdateForm(forms.ModelForm):
    reassign_usertype = forms.ChoiceField(
        choices=USERTYPE_CHOICES,
        required=False,
        label="Reassign To"
    )
    status = forms.ChoiceField(
        choices=REQUEST_STATUS_CHOICES,
        label="Status"
    )
    users_status = forms.ChoiceField(
        choices=[("rejected", "Rejected"), ("approved", "Completed")],
        required=False,
        label="Status"
    )
    description = forms.CharField(
        widget=TinyMCE(attrs={"cols": 80, "rows": 15}),
        required=True,
        label="Description"
    )
    remark = forms.CharField(
        widget=TinyMCE(attrs={"cols": 80, "rows": 15}),
        required=True,
        label="Remark"
    )
    user_flow = forms.MultipleChoiceField(
        choices=USERTYPE_CHOICES,
        widget=forms.MultipleHiddenInput(),
        required=False
    )
    is_request_closed_by_users = forms.ChoiceField(
        choices=CHOICES,
        required=False,
        label="Did you want to assign the request to HR",
        initial="false"
    )
    end_request_flow = forms.ChoiceField(
        choices=CHOICES,
        required=False,
        label="End request flow and send to creator",
        widget=forms.RadioSelect,
        initial="false"
    )
    share_request = forms.ChoiceField(
        choices=[("no", "No"), ("yes", "Yes")],
        required=False,
        label="Did you want to share this request?"
    )
    alternative_description = forms.CharField(
        widget=TinyMCE(attrs={"cols": 80, "rows": 15}),
        required=True,
        label="Request Summary"
    )

    class Meta:
        model = RequestSubmission
        fields = [
            'title', 'description', 'alternative_description', 'attachment',
            'status', 'remark', 'user_flow', 'reassign_usertype',
            'share_request', 'request_shared_usertype', 'is_request_closed_by_users',
            'end_request_flow'
        ]

    def __init__(self, *args, **kwargs):
        self.usertype = kwargs.pop('usertype', None)
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        # Disable certain fields for all users
        for field in ['title', 'description', 'attachment']:
            if field in self.fields:
                self.fields[field].disabled = True

        # Make alternative_description required only for HR
        if self.usertype == "hr":
            self.fields['alternative_description'].required = True
        else:
            self.fields['alternative_description'].required = False

        # COO-specific fields
        if self.usertype != "coo":
            self.fields.pop('status', None)
            self.fields.pop('reassign_usertype', None)

        # HR-specific logic for end_request_flow
        if self.usertype == "hr" and instance:
            self.fields['end_request_flow'].widget = forms.RadioSelect()
            self.fields['users_status'] = forms.ChoiceField(
                choices=[("rejected", "Rejected"), ("approved", "Completed")],
                required=False,
                label="Final Status"
            )
            hr_history_count = instance.status_history.filter(usertype="hr").count()
            if hr_history_count == 0:
                self.fields.pop('remark', None)
            else:
                self.fields.pop('alternative_description', None)
        else:
            self.fields['end_request_flow'].widget = forms.HiddenInput()

        # Non-HR/COO/branch_staff users
        if self.usertype not in ["hr", "coo", "branch_staff"]:
            self.fields.pop('status', None)
            self.fields['users_status'] = forms.ChoiceField(
                choices=[("rejected", "Rejected"), ("approved", "Completed")],
                required=False,
                label="Status"
            )
        else:
            if self.usertype != "hr":
                self.fields.pop('users_status', None)

        # COO specific tweaks
        if self.usertype == "coo" and 'remark' in self.fields:
            self.fields['remark'].required = False

        # Share request logic
        if self.usertype == "hr" and instance:
            coo_history = instance.status_history.exclude(
                usertype__in=["hr", "branch_staff"]
            ).order_by("-date").first()

            if not coo_history or coo_history.status not in ["approved", "rejected"]:
                self.fields.pop("share_request", None)
                self.fields.pop("request_shared_usertype", None)
        else:
            self.fields.pop("share_request", None)
            self.fields.pop("request_shared_usertype", None)

        # Initialize user_flow
        if instance and 'user_flow' in self.fields:
            self.fields['user_flow'].initial = instance.usertype_flow or []

    def clean_user_flow(self):
        return [x for x in self.cleaned_data.get("user_flow", []) if x]

    def clean(self):
        cleaned_data = super().clean()

        # Validation logic
        re_assign = self.data.get("re_assign")
        reassign_usertype = cleaned_data.get("reassign_usertype")
        if "reassign_usertype" in self.fields and re_assign == "yes" and not reassign_usertype:
            self.add_error("reassign_usertype", "This field is required when re-assigning.")

        share_request = cleaned_data.get("share_request")
        shared_users = cleaned_data.get("request_shared_usertype")
        if "request_shared_usertype" in self.fields and share_request == "yes" and not shared_users:
            self.add_error("request_shared_usertype", "Please select at least one usertype to share the request with.")

        end_request_flow = cleaned_data.get("end_request_flow")
        status = cleaned_data.get("status")
        users_status = cleaned_data.get("users_status")
        
        # HR validation for end_request_flow
        if self.usertype == "hr" and end_request_flow == "true":
            # For HR users, check if users_status is provided
            if not users_status:
                self.add_error("users_status", "Final status is required when ending request flow.")
            
            # If status field exists for HR, validate it too
            if "status" in self.fields and status not in ["approved", "rejected"]:
                self.add_error("status", "Status must be 'Completed' or 'Rejected' when ending request flow.")

        # Non-HR/COO/branch_staff users validation
        if self.usertype not in ["hr", "coo", "branch_staff"]:
            is_request_closed_by_users = cleaned_data.get("is_request_closed_by_users")
            users_status = cleaned_data.get("users_status")
            if is_request_closed_by_users == "true" and not users_status:
                self.add_error("users_status", "This field is required when closing the request.")

        return cleaned_data
    

class SyllabusMasterForm(forms.ModelForm):
    class Meta:
        model = SyllabusMaster
        fields = ['order_id', 'course', 'month', 'week', 'title',]

    
class SyllabusForm(forms.ModelForm):
    description = forms.CharField(
        widget=TinyMCE(attrs={"cols": 80, "rows": 5, "class": "tinymce"}),
        required=False,
        label="Description"
    )
    homework = forms.CharField(
        widget=TinyMCE(attrs={"cols": 80, "rows": 5, "class": "tinymce"}),
        required=False,
        label="Homework"
    )
    attachment_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter attachment URL'})
    )

    class Meta:
        model = Syllabus
        fields = ['order_id', 'title',  'attachment_url', 'description', 'homework',]
        widgets = {
            'order_id': forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}),
        }


SyllabusFormSet = inlineformset_factory(
    SyllabusMaster,
    Syllabus,
    form=SyllabusForm,
    extra=1, 
    can_delete=True  
)


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['student', 'subject', 'start_date', 'end_date', 'attachment', 'reason', 'status']
        widgets = {
            'start_date': forms.DateInput(
                attrs={'class': 'form-control'},
                format='%d/%m/%Y'
            ),
            'end_date': forms.DateInput(
                attrs={'class': 'form-control'},
                format='%d/%m/%Y'
            ),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Ensure initial values show as DD/MM/YYYY
        if self.instance and self.instance.pk:
            if self.instance.start_date:
                self.fields['start_date'].initial = self.instance.start_date.strftime('%d/%m/%Y')
            if self.instance.end_date:
                self.fields['end_date'].initial = self.instance.end_date.strftime('%d/%m/%Y')

        # Student: full editable form (except status)
        if user and user.usertype == "student":
            allowed_fields = ['subject', 'start_date', 'end_date', 'attachment', 'reason']
            for field in list(self.fields.keys()):
                if field not in allowed_fields:
                    self.fields.pop(field)

        # Mentor/Teacher: lock fields but keep values
        if user and user.usertype in ["mentor", "teacher"]:
            for field in ['start_date', 'end_date', 'attachment', 'subject', 'reason']:
                if field in self.fields:
                    # Readonly: value stays visible + submitted
                    self.fields[field].widget.attrs['readonly'] = True

        # On create: remove status
        if not self.instance.pk and "status" in self.fields:
            self.fields.pop("status")

    def clean_start_date(self):
        data = self.cleaned_data['start_date']
        if isinstance(data, str):
            return datetime.strptime(data, "%d/%m/%Y").date()
        return data

    def clean_end_date(self):
        data = self.cleaned_data['end_date']
        if isinstance(data, str):
            return datetime.strptime(data, "%d/%m/%Y").date()
        return data
    


class FeedbackAnswerForm(forms.ModelForm):
    class Meta:
        model = FeedbackAnswer
        fields = ('answer_value', "answer")
        widgets = {
            'answer_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter rating or value',
                'min': 1
            }),
            'answer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your answer'
            }),
        }
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['DELETE'] = forms.BooleanField(required=False)


FeedbackAnswerFormSet = inlineformset_factory(
    FeedbackQuestion,
    FeedbackAnswer,
    form=FeedbackAnswerForm,
    extra=1,
    can_delete=True,  
)

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['student', 'comment'] 


class PlacementHistoryForm(forms.ModelForm):
    # Use a separate read-only field just for displaying student name
    student_display = forms.CharField(
        label="Student",
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = PlacementHistory
        fields = [
            'student_display',  # display-only field
            'company_name', 'designation', 'interview_type',
            'interview_date', 'interview_status', 'attended_status',
            'joining_status', 'joining_date'
        ]

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        if student:
            # store Admission instance for saving
            self._student_instance = student
            # display student's name or identifier
            self.fields['student_display'].initial = getattr(student, 'full_name', str(student))
        else:
            # fallback if no student passed
            self.fields['student_display'].initial = "Unknown Student"

    def save(self, commit=True):
        instance = super().save(commit=False)
        # ensure the real Admission instance is assigned to model FK
        if hasattr(self, '_student_instance'):
            instance.student = self._student_instance
        if commit:
            instance.save()
        return instance
    

class PublicMessageForm(forms.ModelForm):
    class Meta:
        model = PublicMessage
        fields = ("message_type", "filter_type", "branch", "course", "message")
        widgets = {
            'message_type': forms.Select(attrs={'class': 'form-control'}),
            'filter_type': forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleFilterFields()'}),
            'branch': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'course': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
        

class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get("scope")
        branches = cleaned_data.get("branch")
        date = cleaned_data.get("date")

        # Validate branch selection for branch-wise holidays
        if scope == "branch" and not branches:
            self.add_error("branch", "Please select at least one branch.")

        # Prevent multiple holidays on the same date
        if date and Holiday.objects.exclude(pk=self.instance.pk).filter(date=date).exists():
            self.add_error("date", "A holiday already exists for this date.")

        return cleaned_data


class EventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name != 'branch' and field_name != 'course':  # These already have classes in widgets
                field.widget.attrs['class'] = 'form-control'
    
    class Meta:
        model = Event
        fields = ("event_type", "filter_type", "title", "branch", "course", "image", "url")
        widgets = {
            'filter_type': forms.Select(attrs={'onchange': 'toggleFilterFields()'}),
            'branch': forms.SelectMultiple(),
            'course': forms.SelectMultiple(),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    
class StateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = "__all__"

    
class TaxForm(forms.ModelForm):
    class Meta:
        model = Tax
        fields = "__all__"
