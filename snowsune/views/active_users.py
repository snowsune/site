from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from tracking.models import Visitor


def active_users_view(request):
    """Return the number of currently active users (sessions started in last 30 minutes)"""

    # Consider users active if they started a session in the last 30 minutes
    # This is more realistic than counting non-expired sessions (which can last weeks)
    now = timezone.now()
    thirty_minutes_ago = now - timedelta(minutes=30)

    # Count unique IPs that started sessions in the last 30 minutes
    active_users = (
        Visitor.objects.filter(
            start_time__gte=thirty_minutes_ago,  # Session started recently
            start_time__lte=now,  # Session started before now
        )
        .values("ip_address")
        .distinct()
        .count()
    )

    return JsonResponse({"active_users": active_users, "timestamp": now.isoformat()})
