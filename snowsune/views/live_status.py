import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.db.models import Q, Count
from datetime import timedelta
from tracking.models import Visitor
from snowsune.models import SiteSetting


@csrf_exempt
@require_http_methods(["GET"])
@cache_page(30)  # Cache for 30 seconds
def live_status_view(request):
    """Return combined live status data including active users and Home Assistant sensor"""

    # Get active users count
    now = timezone.now()
    fifteen_minute_cutoff = now - timedelta(minutes=15)
    active_users = (
        Visitor.objects.filter(start_time__gte=fifteen_minute_cutoff)
        .distinct("session_key")
        .order_by("session_key")
        .count()
    )

    # Get Home Assistant server offset
    server_offset = None
    ha_url_setting = SiteSetting.objects.filter(key="HOME_ASSISTANT_URL").first()
    ha_token_setting = SiteSetting.objects.filter(key="HOME_ASSISTANT_TOKEN").first()

    if ha_url_setting and ha_token_setting:
        try:
            headers = {
                "Authorization": f"Bearer {ha_token_setting.value}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{ha_url_setting.value}/api/states/sensor.server_offset_percentage",
                headers=headers,
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                server_offset = data.get("state", "Unknown")
            else:
                server_offset = "Error"

        except Exception:
            server_offset = "Offline"

    return JsonResponse(
        {
            "active_users": active_users,
            "server_offset": server_offset,
            "timestamp": now.isoformat(),
            "cached": True,
        }
    )
