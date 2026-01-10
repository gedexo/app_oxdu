from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from datetime import timedelta

class UpdateLastSeenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update only if last update was more than 1 minute ago
            # This reduces database writes
            now = timezone.now()
            should_update = (
                not request.user.last_seen or 
                request.user.last_seen < now - timedelta(minutes=1)
            )
            
            if should_update:
                request.user.last_seen = now
                request.user.save(update_fields=['last_seen'])