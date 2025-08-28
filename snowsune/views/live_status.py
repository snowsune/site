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
from bs4 import BeautifulSoup
from django.core.cache import cache


def get_ko_fi_progress():
    """
    Get Ko-fi progress
    Uses django cache manually!
    """

    cache_key = "ko_fi_progress"
    cached_value = cache.get(cache_key)

    if cached_value is not None:
        return cached_value

    ko_fi_url_setting = SiteSetting.objects.filter(key="KO_FI_URL").first()

    if not ko_fi_url_setting:
        return "?"

    try:
        ko_fi_url = ko_fi_url_setting.value

        # Fetch Ko-fi page and extract progress
        headers = {"User-Agent": "Mozilla/5.0 (compatible; SnowsuneBot/1.0)"}
        response = requests.get(ko_fi_url, headers=headers, timeout=5)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            progress_block = soup.find("div", class_="text-left kfds-btm-mrgn-8")

            if progress_block:
                progress_text = progress_block.get_text(strip=True)
                # Extract percentage from text like "75% of goal"
                if "%" in progress_text:
                    result = progress_text.split("%")[0]
                else:
                    result = "?"
            else:
                result = "?"
        else:
            result = "?"

    except Exception as e:
        print(f"Error fetching Ko-fi progress: {e}")
        result = "?"

    # Cache the result for 30 minutes
    cache.set(cache_key, result, 1800)
    return result


@csrf_exempt
@require_http_methods(["GET"])
@cache_page(30)  # Cache for 30 seconds
def live_status_view(request):
    """
    Active users, Home Assistant server offset, and Ko-fi progress
    """
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

    # Get Ko-fi progress
    try:
        ko_fi_progress = get_ko_fi_progress()
    except Exception:
        ko_fi_progress = "?"

    return JsonResponse(
        {
            "active_users": active_users,
            "server_offset": server_offset,
            "ko_fi_progress": ko_fi_progress,
            "timestamp": now.isoformat(),
            "cached": True,
        }
    )
