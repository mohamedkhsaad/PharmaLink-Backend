from django.utils import timezone
from datetime import timedelta
from .models import Session

class SessionExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Perform actions before the view is called
        # Get all sessions
        sessions = Session.objects.all()
        for session in sessions:
            # Check if session has expired
            if session.created_at < timezone.now() - timedelta(hours=4):
                session.ended = True
                session.save()
        
        response = self.get_response(request)
        return response
