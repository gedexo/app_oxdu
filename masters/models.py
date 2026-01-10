import threading
from django.db.models import Q
import threading
from tinymce.models import HTMLField
from django.contrib.sites.models import Site
from django.core.validators import FileExtensionValidator

from core.base import BaseModel
from core.choices import SYLLABUS_MONTH_CHOICE, SYLLABUS_WEEK_CHOICE, MONTH_LIST_CHOICES, USERTYPE_CHOICES, REQUEST_SUBMISSION_STATUS_CHOICES, CHOICES, USERTYPE_FLOW_CHOICES, BATCH_STATUS_CHOICES, LEAVE_STATUS_CHOICES, RATING_CHOICES, FEEDBACK_TYPE_CHOICES, INTERVIEW_STATUS_CHOICES, BOOL_CHOICES

from django.db import models
from django.urls import reverse_lazy

from admission.utils import send_sms


class Batch(BaseModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, null=True)
    course =models.ForeignKey("masters.Course", on_delete=models.CASCADE, null=True)
    batch_name = models.CharField(max_length=120)
    starting_time = models.TimeField(blank=True, null=True)
    ending_time = models.TimeField(blank=True, null=True)
    starting_date = models.DateField(null=True)
    ending_date = models.DateField(null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=128, choices=BATCH_STATUS_CHOICES, default="in_progress")

    def __str__(self):
        return f"{self.batch_name} - {self.course.name}"
    
    def get_completed_students(self):
        return self.admission_set.filter(stage_status='completed')
    
    def get_batch_student_count(self):
        from admission.models import Admission
        students = Admission.objects.filter(is_active=True, stage_status="active", batch=self).count()
        return students

    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:batch_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:batch_detail", kwargs={"pk": self.pk})    
    
    def get_update_url(self):
        return reverse_lazy("masters:batch_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:batch_delete", kwargs={"pk": self.pk})
    
    
class Course(BaseModel):
    name = models.CharField(max_length=120)
    fees = models.PositiveIntegerField()
    brochure = models.FileField(null=True, blank=True, upload_to="brochure/", validators=[FileExtensionValidator(['pdf'])])
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:course_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:course_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:course_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:course_delete", kwargs={"pk": self.pk})
    

class PDFBookResource(BaseModel):
    course = models.ForeignKey("masters.Course", on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.course) 
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:pdf_book_resource_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:pdf_book_resource_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:pdf_book_resource_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:pdf_book_resource_delete", kwargs={"pk": self.pk})
    

class PdfBook(BaseModel):
    resource = models.ForeignKey("masters.PDFBookResource", on_delete=models.CASCADE)
    name = models.CharField(max_length=180)
    pdf = models.FileField(upload_to="pdf/")
    
    def __str__(self):
        return self.name
    
    # @staticmethod
    # def get_list_url():
    #     return reverse_lazy("masters:pdf_book_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:pdf_book_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:pdf_book_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:pdf_book_delete", kwargs={"pk": self.pk})
    

class SyllabusMaster(BaseModel):
    order_id = models.PositiveIntegerField(null=True,)
    course = models.ForeignKey("masters.Course", on_delete=models.CASCADE, null=True)
    month = models.CharField(max_length=120, choices=SYLLABUS_MONTH_CHOICE)
    week = models.CharField(max_length=120, choices=SYLLABUS_WEEK_CHOICE, null=True)
    title = models.CharField(max_length=120, null=True)

    def __str__(self):
        return f"{self.course} - {self.month} - {self.week} - {self.title}"
    
    class Meta:
        ordering = ['order_id'] 
        verbose_name = 'Syllabus Master'
        verbose_name_plural = 'Syllabus Masters'
        unique_together = ('course', 'order_id')
        constraints = [
            models.UniqueConstraint(fields=['course', 'month', 'week'], name='unique_course_month')
        ]
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:syllabus_master_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:syllabus_master_detail", kwargs={"pk": self.pk})
    
    @staticmethod
    def get_create_url():
        return reverse_lazy("masters:syllabus_master_create")
    
    def get_update_url(self):
        return reverse_lazy("masters:syllabus_master_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:syllabus_master_delete", kwargs={"pk": self.pk})
    

class Syllabus(BaseModel):
    syllabus_master = models.ForeignKey("masters.SyllabusMaster", on_delete=models.CASCADE, null=True)
    order_id = models.PositiveIntegerField(null=True)
    title = models.CharField(max_length=120)
    attachment_url = models.URLField(blank=True, null=True)
    description = HTMLField(blank=True, null=True)
    homework = HTMLField(blank=True, null=True)

    def __str__(self):
        return str(self.title) 
    
    class Meta:
        ordering = ['order_id'] 
        verbose_name = 'Syllabus'
        verbose_name_plural = 'Syllabuses'
        

    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:syllabus_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:syllabus_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_create_url():
        return reverse_lazy("masters:syllabus_create")
    
    def get_update_url(self):
        return reverse_lazy("masters:syllabus_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:syllabus_delete", kwargs={"pk": self.pk})



class BatchSyllabusStatus(BaseModel):
    SYLLABUS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    batch = models.ForeignKey("masters.Batch", on_delete=models.CASCADE)
    syllabus = models.ForeignKey("masters.Syllabus", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.User", limit_choices_to={'is_active': True}, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=SYLLABUS_STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ['batch', 'syllabus', 'user']
        verbose_name_plural = "Batch Syllabus Statuses"

    def __str__(self):
        return f"{self.batch.batch_name} - {self.syllabus.title} - {self.user.get_full_name()}"
    
    def get_user_status(self, user=None):
        
        from django.contrib.auth import get_user
        from .models import BatchSyllabusStatus
        
        if not user:
            user = get_user()
        
        try:
            status_obj = BatchSyllabusStatus.objects.get(
                syllabus=self,
                user=user,
                batch=user.batch
            )
            return status_obj.status
        except BatchSyllabusStatus.DoesNotExist:
            return 'pending'
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:batch_syllabus_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:batch_syllabus_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:batch_syllabus_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:batch_syllabus_delete", kwargs={"pk": self.pk})
    

class ComplaintRegistration(BaseModel):
    COMPALINT_TYPE_CHOICES = [
        ("general", "General"),
        ("academic", "Academic"),
        ("other", "Other")
    ]
    complaint_type = models.CharField(max_length=15, choices=COMPALINT_TYPE_CHOICES, default="general")
    complaint = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=[
            ("Complaint Registered", "Complaint Registered"),
            ("In Progress", "In Progress"),
            ("Resolved", "Resolved"),
            ("Closed", "Closed")
        ],
        default="Complaint Registered"
    )
    
    def __str__(self):
        return str(self.complaint_type) 
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:complaint_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:complaint_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:complaint_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:complaint_delete", kwargs={"pk": self.pk})

    
class ChatSession(BaseModel):
    sender = models.ForeignKey("accounts.User", related_name="sent_messages", on_delete=models.CASCADE, null=True)
    recipient = models.ForeignKey("accounts.User", related_name="received_messages", on_delete=models.CASCADE, null=True)
    attachment = models.FileField(
        upload_to='chat_attachments/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])]
    )
    message = models.TextField()
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Add this field to track who deleted the message
    deleted_by_ids = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.sender} to {self.recipient}"
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:chat_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:chat_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:chat_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:chat_delete", kwargs={"pk": self.pk})
    
    # Helper methods
    def is_deleted_by(self, user):
        """Check if message is deleted by a specific user"""
        return user.id in self.deleted_by_ids
    
    def delete_for(self, user):
        """Mark message as deleted for a specific user"""
        if user.id not in self.deleted_by_ids:
            self.deleted_by_ids.append(user.id)
            self.save(update_fields=['deleted_by_ids'])

    
class Update(BaseModel):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="updates/")
    description = HTMLField()
    is_notification = models.BooleanField(default=True, help_text="Show as notification")
    notification_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.is_notification and not self.notification_sent:
            # Send WhatsApp notifications in background
            threading.Thread(target=self._send_notifications_background).start()

    def _send_notifications_background(self):
        """Run background thread to send messages"""
        try:
            self.send_whatsapp_notifications()
            self.notification_sent = True
            self.save(update_fields=["notification_sent"])
        except Exception as e:
            print("Error sending WhatsApp notifications:", e)

    def send_whatsapp_notifications(self):
        from admission.models import Admission

        current_site = Site.objects.get_current()
        update_url = f"https://{current_site.domain}{self.get_absolute_url()}"
        message = f"📢 *New Update: {self.title}*\n\nCheck details here:\n{update_url}"

        students = Admission.objects.filter(
            whatsapp_number__isnull=False,
            stage_status="active",
            user__is_active=True
        ).values_list("whatsapp_number", flat=True)

        for number in students:
            send_sms(number, message)

    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:update_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:update_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:update_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:update_delete", kwargs={"pk": self.pk})

    @classmethod
    def get_unread_notifications(cls, user):
        """Get unread notifications for a user"""
        # You might want to implement user-specific notification tracking
        # For now, return all active notifications
        return cls.objects.filter(is_active=True, is_notification=True).order_by('-created')[:10]
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user"""
        return cls.get_unread_notifications(user).count()

    
class NotificationReadStatus(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    update = models.ForeignKey(Update, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'update']
        verbose_name_plural = "Notification Read Status"

    def __str__(self):
        return f"{self.user} read {self.update}"


class PlacementRequest(BaseModel):
    student = models.OneToOneField("admission.Admission", on_delete=models.CASCADE, null=True)
    resume = models.URLField(
        verbose_name="Resume Link",
        help_text="Please provide a link to your resume."
    )
    portfolio_link = models.URLField(
        verbose_name="Portfolio Link",
        blank=True,
        help_text="Link to your portfolio or work samples"
    )
    behance_link = models.URLField(
        verbose_name="Behance Profile Link",
        blank=True,
        help_text="Link to your Behance portfolio"
    )
    experience = models.TextField(
        verbose_name="Experience",
        blank=True,
        help_text="Please provide details of your experience, if any."
    )

    status  = models.CharField(
        max_length=30,
        choices=[
            ("Request Send", "Request Send"),
            ("Under Review", "Under Review"),
            ("Completed", "Completed"),
            ("Rejected", "Rejected")
        ],
        default="Request Send"
    )

    
    def __str__(self):
        return self.student.fullname() if self.student else "Placement Request"
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:placement_request_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:placement_request_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:placement_request_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:placement_request_delete", kwargs={"pk": self.pk})
    

class Activity(BaseModel):
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
        ordering = ["name"]

    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:activity_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:activity_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:activity_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:activity_delete", kwargs={"pk": self.pk})
    

class BranchActivity(BaseModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, null=True)
    activity = models.ForeignKey("masters.Activity", on_delete=models.CASCADE)
    month = models.CharField(max_length=120, choices=MONTH_LIST_CHOICES, null=True)
    point = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.branch} - {self.activity} ({self.point} pts)"
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:branch_activity_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:branch_activity_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:branch_activity_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:branch_activity_delete", kwargs={"pk": self.pk})
    

def generate_request_submission_no(prefix="REQ"):
    last_request = RequestSubmission.objects.filter(request_id__startswith=prefix).order_by('-request_id').first()

    if last_request and last_request.request_id:
        try:
            last_id = int(last_request.request_id.replace(prefix, ""))
            next_id = last_id + 1
        except ValueError:
            next_id = 1
    else:
        next_id = 1

    return f"{prefix}{str(next_id).zfill(4)}"


class RequestSubmission(BaseModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, null=True)
    request_id = models.CharField(max_length=128, unique=True, null=True)
    branch_staff = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        limit_choices_to={"user__usertype": "branch_staff"},
    )
    title = models.CharField(max_length=180, null=True)
    description = HTMLField(null=True)
    alternative_description = HTMLField(null=True, blank=True,)
    attachment = models.FileField(upload_to="request_submissions/", blank=True, null=True)
    current_usertype = models.CharField(max_length=30, choices=USERTYPE_FLOW_CHOICES, null=True)
    request_shared_usertype = models.ManyToManyField(
        "employees.Employee",
        related_name="shared_requests",
        blank=True
    )
    usertype_flow = models.JSONField(default=list, null=True)
    status = models.CharField(max_length=30, choices=REQUEST_SUBMISSION_STATUS_CHOICES, default="forwarded")
    created_by = models.ForeignKey("employees.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_submissions")
    updated_by = models.ForeignKey("employees.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_submissions")
    is_request_closed_by_users = models.CharField(max_length=80, choices=CHOICES, default='false', verbose_name="Request Close By User")
    is_request_completed = models.CharField(max_length=80, choices=CHOICES, default='false', verbose_name="Request Completed")

    def __str__(self):
        return f"{self.title}"
    
    class Meta:
        ordering = ['-updated']
        verbose_name = "Request Submission"
        verbose_name_plural = "Request Submissions"

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = generate_request_submission_no()
        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        """Return boolean for completion status"""
        return self.is_request_completed == 'true'

    @property
    def coo_status(self):
        coo_status = self.status_history.filter(usertype="coo").order_by("-date").first()
        return coo_status.status if coo_status else "Pending"

    @property
    def hr_status(self):
        hr_status = self.status_history.filter(usertype="hr").order_by("-date").first()
        return hr_status.status if hr_status else "Pending"

    @property
    def is_approved_or_rejected_for_current_user(self):
        """Check if HR approved/rejected and assigned to the logged-in usertype."""
        from django.middleware import get_current_request

        request = get_current_request()
        if not request or not hasattr(request.user, "profile"):
            return False

        user_profile = request.user.profile
        return self.status in ['approved', 'rejected'] and RequestSubmissionStatusHistory.objects.filter(
            submission=self,
            usertype='hr',
            next_usertype=user_profile.user.usertype,
        ).exists()

    def is_processed_by(self, user_profile):
        return RequestSubmissionStatusHistory.objects.filter(
            submission=self,
            usertype=user_profile.user.usertype,
            submitted_users=user_profile
        ).exists()

    def get_list_url(self):
        return reverse_lazy("masters:my_request_submission_list")

    def get_absolute_url(self):
        return reverse_lazy("masters:request_submission_detail", kwargs={"pk": self.pk})
    
    @staticmethod
    def get_create_url():
        return reverse_lazy("masters:request_submission_create")

    def get_update_url(self):
        return reverse_lazy("masters:request_submission_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("masters:request_submission_delete", kwargs={"pk": self.pk})

    def get_next_user_in_flow(self, current_user_usertype=None):
        if not self.usertype_flow:
            return None

        submitted_usertypes = self.status_history.values_list('usertype', flat=True)

        # Handle normal flow
        try:
            current_index = self.usertype_flow.index(current_user_usertype)
            for next_usertype in self.usertype_flow[current_index + 1:]:
                if next_usertype not in submitted_usertypes:
                    return next_usertype
        except ValueError:
            pass

        return None


class RequestSubmissionStatusHistory(BaseModel):
    submission = models.ForeignKey(RequestSubmission, on_delete=models.CASCADE, related_name='status_history')
    user = models.ForeignKey("employees.Employee", on_delete=models.SET_NULL, null=True, blank=True)
    submitted_users = models.ManyToManyField("employees.Employee", related_name="submitted_users")
    usertype = models.CharField(max_length=30, choices=USERTYPE_FLOW_CHOICES)
    next_usertype = models.CharField(max_length=30, choices=USERTYPE_FLOW_CHOICES)
    status = models.CharField(max_length=20, choices=REQUEST_SUBMISSION_STATUS_CHOICES, default="forwarded")
    remark = HTMLField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.submission.title} - {self.usertype} - {self.status}"


class LeaveRequest(BaseModel):
    student = models.ForeignKey("admission.Admission", on_delete=models.CASCADE, null=True)
    subject = models.CharField(max_length=200, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    attachment = models.FileField(upload_to="leave_attachments/", blank=True, null=True)
    status = models.CharField(
        max_length=30,
        choices=LEAVE_STATUS_CHOICES,
        default="pending"
    )
    approved_by = models.ForeignKey("employees.Employee", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Submitted By",)
    approved_date = models.DateTimeField(null=True, blank=True, verbose_name="Submitted Date",)

    def __str__(self):
        return f"Leave Request by {self.student.fullname()} from {self.start_date} to {self.end_date}"
    
    def is_active_on(self, date):
        return self.status == 'approved' and self.start_date <= date <= self.end_date
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:leave_request_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:leave_request_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:leave_request_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:leave_request_delete", kwargs={"pk": self.pk})


class FeedbackQuestion(BaseModel):
    feedback_type = models.CharField(choices=FEEDBACK_TYPE_CHOICES,max_length=100)
    order = models.PositiveIntegerField()
    question = models.CharField(max_length=255)

    class Meta:
        ordering = ['order',]
        verbose_name = 'Feedback Question'
        verbose_name_plural = 'Feedback Questions'
        constraints = [
            models.UniqueConstraint(
                fields=['feedback_type', 'order'],
                name='unique_active_feedback_question_per_type',
                condition=Q(is_active=True)
            )
        ]

    def __str__(self):
        return self.question
    
    @staticmethod
    def get_active_questions():
        return FeedbackQuestion.objects.filter(is_active=True).order_by('order', 'created')
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:feedback_question_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:feedback_question_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:feedback_question_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:feedback_question_delete", kwargs={"pk": self.pk})


class FeedbackAnswer(BaseModel):
    question = models.ForeignKey("masters.FeedbackQuestion", on_delete=models.CASCADE)
    answer_value = models.PositiveIntegerField()
    answer = models.CharField(max_length=180)

    def __str__(self):
        return self.answer
    
    class Meta:
        verbose_name = 'Feedback Answer'
        verbose_name_plural = 'Feedback Answers'
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'answer_value'],
                name='unique_active_feedback_answer_per_question',
                condition=Q(is_active=True)  
            )
        ]

    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:feedback_question_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:feedback_answer_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:feedback_answer_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:feedback_answer_delete", kwargs={"pk": self.pk})
    

class Feedback(BaseModel):
    student = models.ForeignKey("admission.Admission", on_delete=models.CASCADE)
    question = models.ForeignKey("masters.FeedbackQuestion", on_delete=models.CASCADE)
    answer = models.ForeignKey("masters.FeedbackAnswer", on_delete=models.CASCADE)
    comment = models.TextField()

    def __str__(self):
        return f"{self.student} - {self.question}"
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:feedback_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:feedback_detail", kwargs={"pk": self.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:feedback_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:feedback_delete", kwargs={"pk": self.pk})


class PlacementHistory(BaseModel):
    student = models.ForeignKey("admission.Admission", on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    designation = models.CharField(max_length=200)
    interview_type = models.CharField(max_length=200)
    interview_date = models.DateField()
    interview_status = models.CharField(max_length=200, choices=INTERVIEW_STATUS_CHOICES)
    attended_status = models.CharField(max_length=200, choices=CHOICES)
    joining_status = models.CharField(max_length=200, choices=CHOICES, default="false")
    joining_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.company_name}"
    
    class Meta:
        ordering = ['-created']
        verbose_name = 'Placement History'
        verbose_name_plural = 'Placement Histories'
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:placement_history_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:student_placement_history", kwargs={"pk": self.student.pk})
    
    def get_update_url(self):
        return reverse_lazy("masters:placement_history_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:placement_history_delete", kwargs={"pk": self.pk})
    

class PublicMessage(BaseModel):
    MESSAGE_TYPE_CHOICES = [
        ("students", "Students"),
        ("parents", "Parents"),
        ("all", "All"),
    ]
    
    FILTER_TYPE_CHOICES = [
        ("branch", "By Branch"),
        ("course", "By Course"),
        ("branch_course", "By Branch & Course"),
    ]
    
    message_type = models.CharField(max_length=200, choices=MESSAGE_TYPE_CHOICES, default="all")
    filter_type = models.CharField(max_length=200, choices=FILTER_TYPE_CHOICES, default="all")
    branch = models.ManyToManyField("branches.Branch", blank=True)
    course = models.ManyToManyField("masters.Course", blank=True) 
    message = HTMLField()
    sent = models.BooleanField(default=False)

    def __str__(self):
        # Return a simple string representation
        return f"PublicMessage {self.id}"

    class Meta: 
        ordering = ['-created']
        verbose_name = 'Public Message'
        verbose_name_plural = 'Public Messages'

    def get_target_admissions(self):
        """
        Returns the queryset of admissions who should receive this message
        based on the filter criteria
        """
        # Use string reference to avoid circular imports
        from admission.models import Admission
        
        admissions = Admission.objects.all()
        
        # Filter by filter type
        if self.filter_type == "branch" and self.branch.exists():
            branch_ids = self.branch.values_list('id', flat=True)
            admissions = admissions.filter(branch__id__in=branch_ids)
            
        elif self.filter_type == "course" and self.course.exists():
            course_ids = self.course.values_list('id', flat=True)
            admissions = admissions.filter(course__id__in=course_ids)
            
        elif self.filter_type == "branch_course":
            if self.branch.exists() and self.course.exists():
                branch_ids = self.branch.values_list('id', flat=True)
                course_ids = self.course.values_list('id', flat=True)
                admissions = admissions.filter(
                    branch__id__in=branch_ids,
                    course__id__in=course_ids
                )
            elif self.branch.exists():
                branch_ids = self.branch.values_list('id', flat=True)
                admissions = admissions.filter(branch__id__in=branch_ids)
            elif self.course.exists():
                course_ids = self.course.values_list('id', flat=True)
                admissions = admissions.filter(course__id__in=course_ids)
        
        return admissions.distinct()

    def get_phone_numbers(self):
        """
        Get phone numbers based on message type
        """
        admissions = self.get_target_admissions()
        phone_numbers = []
        
        for admission in admissions:
            if self.message_type == "students":
                # Student numbers
                if admission.whatsapp_number:
                    phone_numbers.append(admission.whatsapp_number)
                elif admission.contact_number:
                    phone_numbers.append(admission.contact_number)
                    
            elif self.message_type == "parents":
                # Parent numbers
                if admission.parent_whatsapp_number:
                    phone_numbers.append(admission.parent_whatsapp_number)
                elif admission.parent_contact_number:
                    phone_numbers.append(admission.parent_contact_number)
                    
            elif self.message_type == "all":
                # Both student and parent numbers
                # Student numbers
                if admission.whatsapp_number:
                    phone_numbers.append(admission.whatsapp_number)
                elif admission.contact_number:
                    phone_numbers.append(admission.contact_number)
                
                # Parent numbers
                if admission.parent_whatsapp_number:
                    phone_numbers.append(admission.parent_whatsapp_number)
                elif admission.parent_contact_number:
                    phone_numbers.append(admission.parent_contact_number)
        
        # Remove duplicates and None values
        phone_numbers = list(set([num for num in phone_numbers if num]))
        return phone_numbers

    def send_whatsapp_messages(self):
        """
        Send WhatsApp messages to all target phone numbers
        """
        # Check if instance has been saved
        if not self.pk:
            print("❌ Cannot send messages: PublicMessage instance not saved yet")
            return {
                'sent_count': 0,
                'failed_count': 0,
                'total_numbers': 0,
                'error': 'Instance not saved'
            }
        
        phone_numbers = self.get_phone_numbers()
        sent_count = 0
        failed_count = 0
        
        print(f"Attempting to send message to {len(phone_numbers)} phone numbers")
        
        for phone_number in phone_numbers:
            if not phone_number:
                continue
            
            # Clean phone number (remove spaces, dashes, etc.)
            clean_phone = str(phone_number).strip().replace(' ', '').replace('-', '').replace('+', '')
            
            # Ensure phone number has country code if it's 10 digits
            if not clean_phone.startswith('91') and len(clean_phone) == 10:
                clean_phone = '91' + clean_phone
            
            # Prepare message content
            import re
            clean_message = re.sub('<[^<]+?>', '', self.message)
            clean_message = clean_message.strip()
            
            if not clean_message:
                clean_message = "New message from institution"
            
            # Import send_sms here to avoid circular imports
            from .views import send_sms
            
            # Send WhatsApp message
            success = send_sms(clean_phone, clean_message)
            
            if success:
                sent_count += 1
                print(f"✅ Message sent to {clean_phone}")
            else:
                failed_count += 1
                print(f"❌ Failed to send message to {clean_phone}")
        
        # Update sent status
        if sent_count > 0:
            self.sent = True
            # Use update() to avoid triggering save signals
            PublicMessage.objects.filter(pk=self.pk).update(sent=True)
        
        return {
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_numbers': len(phone_numbers)
        }

    def get_target_description(self):
        """Returns a human-readable description of who will receive the message"""
        admissions_count = self.get_target_admissions().count()
        phone_numbers_count = len(self.get_phone_numbers())
        
        descriptions = []
        
        # Message type description
        if self.message_type == "students":
            descriptions.append(f"Students ({admissions_count} students)")
        elif self.message_type == "parents":
            descriptions.append(f"Parents ({admissions_count} parents)")
        else:
            descriptions.append(f"All ({admissions_count} students & parents)")
        
        # Filter type description
        if self.filter_type == "branch" and self.branch.exists():
            branch_names = [branch.name for branch in self.branch.all()]
            descriptions.append(f"in {', '.join(branch_names)}")
            
        elif self.filter_type == "course" and self.course.exists():
            course_names = [course.name for course in self.course.all()]
            descriptions.append(f"for courses: {', '.join(course_names)}")
            
        elif self.filter_type == "branch_course":
            if self.branch.exists() and self.course.exists():
                branch_names = [branch.name for branch in self.branch.all()]
                course_names = [course.name for course in self.course.all()]
                descriptions.append(f"in {', '.join(branch_names)} for courses: {', '.join(course_names)}")
            elif self.branch.exists():
                branch_names = [branch.name for branch in self.branch.all()]
                descriptions.append(f"in {', '.join(branch_names)}")
            elif self.course.exists():
                course_names = [course.name for course in self.course.all()]
                descriptions.append(f"for courses: {', '.join(course_names)}")
        
        descriptions.append(f"-> {phone_numbers_count} phone numbers")
        
        return " ".join(descriptions)

    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:public_message_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:public_message_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_create_url():
        return reverse_lazy("masters:public_message_create")
    
    def get_update_url(self):
        return reverse_lazy("masters:public_message_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:public_message_delete", kwargs={"pk": self.pk})
    

class Holiday(BaseModel):
    HOLIDAY_SCOPE_CHOICES = [
        ('all', 'All Branches'),
        ('branch', 'Specific Branch'),
    ]
    name = models.CharField(max_length=255)
    date = models.DateField()
    scope = models.CharField(max_length=20, choices=HOLIDAY_SCOPE_CHOICES, default='all')
    branch = models.ManyToManyField(
        'branches.Branch',
        blank=True,
        help_text="Required if scope is branch-wise"
    )
    description = models.TextField(blank=True, null=True)
    is_auto_holiday =  models.BooleanField(default=False, help_text="Automatically created for weekends")

    class Meta:
        ordering = ['-date']
        verbose_name = "Holiday"
        verbose_name_plural = "Holidays"

    def __str__(self):
        return self.name

    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:holiday_list")
    
    def get_update_url(self):
        return reverse_lazy("masters:holiday_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:holiday_delete", kwargs={"pk": self.pk})
    
    @staticmethod
    def get_create_url():
        return reverse_lazy("masters:holiday_create")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:holiday_detail", kwargs={"pk": self.pk})
    
    def is_holiday_for_branch(self, branch):
        """Check if this holiday applies to a specific branch"""
        if self.scope == 'all':
            return True
        return self.branch.filter(id=branch.id).exists()
    
    @staticmethod
    def is_auto_holiday(date_obj):
        """Return True if the given date is Sunday or second Saturday"""
        try:
            # Ensure we have a proper date object
            if isinstance(date_obj, str):
                # Try to parse string date
                from datetime import datetime
                try:
                    date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_obj, '%d-%m-%Y').date()
                    except ValueError:
                        return False, None
            
            # Check if it's a date object with weekday method
            if hasattr(date_obj, 'weekday') and hasattr(date_obj, 'day'):
                # Sunday = 6 (Python weekday: Monday=0, Sunday=6)
                if date_obj.weekday() == 6:
                    return True, "Sunday"
                
                # Second Saturday (Saturday = 5, and day between 8-14)
                if date_obj.weekday() == 5 and 8 <= date_obj.day <= 14:
                    return True, "Second Saturday"
            
            return False, None
            
        except Exception as e:
            print(f"Error in is_auto_holiday: {e}")
            return False, None
    
    @classmethod
    def get_or_create_auto_holiday(cls, date_obj):
        """Get or create automatic holiday record for weekends"""
        is_auto_holiday, holiday_name = cls.is_auto_holiday(date_obj)
        if is_auto_holiday:
            holiday, created = cls.objects.get_or_create(
                date=date_obj,
                is_auto_holiday=True,
                defaults={
                    'name': holiday_name,
                    'scope': 'all',
                    'description': f'Auto-generated holiday: {holiday_name}'
                }
            )
            return holiday
        return None
    

class HeroBanner(BaseModel):
    BANNER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('employee', 'employee'),
        ('all', 'All'),
    ]
    banner_type = models.CharField(max_length=255, choices=BANNER_TYPE_CHOICES, default='student')
    image = models.ImageField(upload_to="hero_banners/")
    url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Hero Banner"
        verbose_name_plural = "Hero Banners"

    def __str__(self):
        return self.banner_type
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:hero_banner_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:hero_banner_detail", kwargs={"pk": self.pk})
    
    @staticmethod
    def get_create_url():
        return reverse_lazy("masters:hero_banner_create")
    
    def get_update_url(self):
        return reverse_lazy("masters:hero_banner_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:hero_banner_delete", kwargs={"pk": self.pk})
    

class Event(BaseModel):
    EVENT_TYPE = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('all', 'All'),
    ]
    FILTER_TYPE_CHOICES = [
        ("branch", "By Branch"),
        ("course", "By Course"),
        ("branch_course", "By Branch & Course"),
    ]
    event_type = models.CharField(max_length=255, choices=EVENT_TYPE, default="all")
    filter_type = models.CharField(max_length=255, choices=FILTER_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    branch = models.ManyToManyField("branches.Branch", blank=True)
    course = models.ManyToManyField("masters.Course", blank=True) 
    image = models.ImageField(upload_to="events/")
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title
    
    @staticmethod
    def get_list_url():
        return reverse_lazy("masters:event_list")
    
    def get_absolute_url(self):
        return reverse_lazy("masters:event_detail", kwargs={"pk": self.pk})
    
    @staticmethod
    def get_create_url():
        return reverse_lazy("masters:event_create")
    
    def get_update_url(self):
        return reverse_lazy("masters:event_update", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        return reverse_lazy("masters:event_delete", kwargs={"pk": self.pk})