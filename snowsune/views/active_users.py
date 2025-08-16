from django.http import JsonResponse
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.db.models import Q, Count
from datetime import timedelta
from tracking.models import Visitor


def active_users_view(request):
    """Return the number of currently active users based on active sessions with filtering"""

    now = timezone.now()

    # Get all active sessions for debugging
    all_sessions = Session.objects.filter(expire_date__gt=now)

    # Count unique visitors active in the last 2 hours
    two_hour_cutoff = now - timedelta(hours=2)
    active_users = (
        Visitor.objects.filter(start_time__gte=two_hour_cutoff)
        .distinct("session_key")
        .order_by("session_key")
        .count()
    )

    return JsonResponse(
        {
            "active_users": active_users,
            "timestamp": now.isoformat(),
        }
    )
