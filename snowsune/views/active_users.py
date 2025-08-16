from django.http import JsonResponse
from django.utils import timezone
from django.contrib.sessions.models import Session


def active_users_view(request):
    """Return the number of currently active users based on active sessions"""

    # Count active (non-expired) sessions
    # This shows users who are actually connected to the site
    now = timezone.now()
    active_users = Session.objects.filter(expire_date__gt=now).count()

    return JsonResponse({"active_users": active_users, "timestamp": now.isoformat()})
