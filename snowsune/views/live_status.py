import json
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from snowsune.models import SiteSetting

logger = logging.getLogger(__name__)


def get_ko_fi_progress():
    """Get Ko-fi progress from SiteSetting."""
    ko_fi_setting = SiteSetting.objects.filter(key="KO_FI_PROGRESS").first()
    if ko_fi_setting:
        try:
            return f"{float(ko_fi_setting.value):.1f}"
        except (ValueError, TypeError):
            return "?"
    return "?"


def get_cloudflare_page_views():
    """
    Fetch today's total request count (page views) from Cloudflare GraphQL Analytics.
    Returns an int or "?" on failure.
    """
    if not all(
        [
            getattr(settings, "CLOUDFLARE_ANALYTICS_API_TOKEN", None),
            getattr(settings, "CLOUDFLARE_ZONE_ID", None),
        ]
    ):
        if settings.DEBUG:
            logger.error("Cloudflare: missing API token or zone ID")
        return "?"

    url = "https://api.cloudflare.com/client/v4/graphql"
    now = timezone.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    query = """
    query {
      viewer {
        zones(filter: {zoneTag: "%s"}) {
          httpRequestsAdaptiveGroups(
            filter: {
              datetime_geq: "%s"
              datetime_leq: "%s"
              requestSource: "eyeball"
            }
            limit: 10000
          ) {
            count
          }
        }
      }
    }
    """ % (
        settings.CLOUDFLARE_ZONE_ID,
        start_of_today.strftime("%Y-%m-%dT%H:%M:%SZ"),
        now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.CLOUDFLARE_ANALYTICS_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"query": query},
            timeout=3,
        )
        if response.status_code != 200:
            if settings.DEBUG:
                logger.error("Cloudflare: HTTP %s %s", response.status_code, response.text[:300])
            return "?"

        data = response.json()
        if data.get("errors"):
            if settings.DEBUG:
                logger.error("Cloudflare GraphQL errors: %s", data.get("errors"))
            return "?"

        zones = data.get("data", {}).get("viewer", {}).get("zones", [])
        if not zones:
            return "?"

        groups = zones[0].get("httpRequestsAdaptiveGroups", [])
        return sum(g.get("count") or 0 for g in groups) if groups else 0
    except Exception as e:
        if settings.DEBUG:
            logger.exception("Cloudflare API error: %s", e)
        else:
            logger.error("Cloudflare API error: %s", e)
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


@csrf_exempt
@require_http_methods(["GET"])
@cache_page(30)
def live_status_view(request):
    """Live status: daily page views from Cloudflare, active users = logged-in Django sessions."""
    # Page views: Cloudflare daily request count (with cache fallback)
    page_views = get_cloudflare_page_views()
    if page_views == "?":
        cached = cache.get("live_status_page_views")
        if cached is not None:
            page_views = cached
        else:
            page_views = "?"
    else:
        cache.set("live_status_page_views", page_views, 3600)

    # Get the active users (using django internal for now)
    logged_in_count = get_active_logged_in_session_count()
    active_users = logged_in_count
    unique_visitors = logged_in_count

    # Home Assistant server offset
    server_offset = None
    ha_url_setting = SiteSetting.objects.filter(key="HOME_ASSISTANT_URL").first()
    ha_token_setting = SiteSetting.objects.filter(key="HOME_ASSISTANT_TOKEN").first()
    if ha_url_setting and ha_token_setting:
        try:
            resp = requests.get(
                f"{ha_url_setting.value}/api/states/sensor.server_offset_percentage",
                headers={"Authorization": f"Bearer {ha_token_setting.value}", "Content-Type": "application/json"},
                timeout=5,
            )
            server_offset = resp.json().get("state", "Unknown") if resp.status_code == 200 else "Error"
        except Exception:
            server_offset = "Offline"

    ko_fi_progress = get_ko_fi_progress()

    response = JsonResponse(
        {
            "active_users": active_users,
            "page_views": page_views,
            "unique_visitors": unique_visitors,
            "server_offset": server_offset,
            "ko_fi_progress": ko_fi_progress,
            "timestamp": timezone.now().isoformat(),
        }
    )
    response["Cache-Control"] = "public, max-age=30"
    response["Vary"] = "Cookie"
    response["Expires"] = (timezone.now() + timedelta(seconds=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    return response
