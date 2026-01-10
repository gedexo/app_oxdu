from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

@receiver(user_logged_in)
def set_last_seen_on_login(sender, request, user, **kwargs):
    """Update last_seen when user logs in"""
    user.last_seen = timezone.now()
    user.save(update_fields=['last_seen'])

@receiver(user_logged_out)
def clear_last_seen_on_logout(sender, request, user, **kwargs):
    """Clear last_seen when user logs out"""
    if user:
        user.last_seen = None
        user.save(update_fields=['last_seen'])