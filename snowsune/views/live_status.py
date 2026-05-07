import logging
from datetime import timedelta

import requests
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from snowsune.models import SiteSetting

logger = logging.getLogger(__name__)


def get_ko_fi_progress():
    ko_fi_setting = SiteSetting.objects.filter(key="KO_FI_PROGRESS").first()
    if ko_fi_setting:
        try:
            return f"{float(ko_fi_setting.value):.1f}"
        except (ValueError, TypeError):
            return "?"
    return "?"


def get_active_logged_in_session_count():
    """Count non-expired Django sessions that have a logged-in user (_auth_user_id)."""
    from django.contrib.sessions.models import Session

    now = timezone.now()
    count = 0
    for session in Session.objects.filter(expire_date__gt=now).iterator(chunk_size=500):
        if session.get_decoded().get("_auth_user_id"):
            count += 1
    return count


def get_server_offset():
    """Home Assistant server offset percentage if configured, else None."""
    ha_url_setting = SiteSetting.objects.filter(key="HOME_ASSISTANT_URL").first()
    ha_token_setting = SiteSetting.objects.filter(key="HOME_ASSISTANT_TOKEN").first()
    if not (ha_url_setting and ha_token_setting):
        return None

    cache_key = "live_status_server_offset"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            f"{ha_url_setting.value}/api/states/sensor.server_offset_percentage",
            headers={"Authorization": f"Bearer {ha_token_setting.value}", "Content-Type": "application/json"},
            timeout=5,
        )
        value = resp.json().get("state", "Unknown") if resp.status_code == 200 else "Error"
    except Exception as e:
        logger.info("Home Assistant server offset unavailable: %s", e)
        value = "Offline"

    cache.set(cache_key, value, 30)
    return value


@csrf_exempt
@require_http_methods(["GET"])
@cache_page(30)
def live_status_view(request):
    active_users = get_active_logged_in_session_count()
    server_offset = get_server_offset()
    ko_fi_progress = get_ko_fi_progress()

    response = JsonResponse(
        {
            "active_users": active_users,
            "server_offset": server_offset,
            "ko_fi_progress": ko_fi_progress,
            "timestamp": timezone.now().isoformat(),
        }
    )
    response["Cache-Control"] = "public, max-age=30"
    response["Vary"] = "Cookie"
    response["Expires"] = (timezone.now() + timedelta(seconds=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    return response

