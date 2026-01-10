from branches.models import Branch
from admission.models import Admission

from django.conf import settings


def main_context(request):
    user = request.user if request.user.is_authenticated else None
    name = user.email if user else None

    loged_branch = user.employee.branch if user and hasattr(user, 'employee') and user.employee else None
    
    admission = None
    if request.user.is_authenticated and request.user.usertype == 'student':
        admission = Admission.objects.filter(user=request.user).select_related('course').first()

    # Updated notification logic with read tracking
    unread_notification_count = 0
    unread_notifications = []
    
    if user and user.is_authenticated:
        try:
            from masters.models import Update, NotificationReadStatus

            all_notifications = Update.objects.filter(
                is_active=True,
                is_notification=True
            ).order_by('-created')[:10]

            # Get updates user has read
            read_updates = NotificationReadStatus.objects.filter(user=user).values_list('update_id', flat=True)

            # Filter unread
            unread_notifications = [n for n in all_notifications if n.id not in read_updates]

            unread_notification_count = len(unread_notifications)

        except Exception as e:
            print(f"Error loading notifications: {e}")
            unread_notifications = []
            unread_notification_count = 0

    return {
        "current_employee": user,
        "default_user_avatar": f"https://ui-avatars.com/api/?name={name or ''}&background=fdc010&color=fff&size=128",
        "app_settings": settings.APP_SETTINGS,
        "loged_branch": loged_branch,
        'admission': admission,
        "unread_notification_count": unread_notification_count,
        "unread_notifications": unread_notifications,
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        "is_student_send_placement_request": (
            admission.is_student_send_placement_request if admission else False
        ),
    }