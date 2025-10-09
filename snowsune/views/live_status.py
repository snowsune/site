import requests
import json
import logging
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from snowsune.models import SiteSetting

logger = logging.getLogger(__name__)


def get_ko_fi_progress():
    """
    Get Ko-fi progress from SiteSetting
    """
    ko_fi_setting = SiteSetting.objects.filter(key="KO_FI_PROGRESS").first()
    if ko_fi_setting:
        try:
            return f"{float(ko_fi_setting.value):.1f}"
        except (ValueError, TypeError):
            return "?"
    else:
        return "?"


def get_cloudflare_analytics():
    """
    Get analytics data from Cloudflare GraphQL Analytics API
    """
    if not all(
        [
            settings.CLOUDFLARE_ANALYTICS_API_TOKEN,
            settings.CLOUDFLARE_ZONE_ID,
            settings.CLOUDFLARE_ACCOUNT_ID,
        ]
    ):
        if settings.DEBUG:
            raise Exception(
                "Cloudflare Analytics API is not configured - missing API token, zone ID, or account ID"
            )
        return {"active_users": "?", "page_views": "?", "unique_visitors": "?"}

    try:
        headers = {
            "Authorization": f"Bearer {settings.CLOUDFLARE_ANALYTICS_API_TOKEN}",
            "Content-Type": "application/json",
        }

        # Use GraphQL Analytics API
        url = "https://api.cloudflare.com/client/v4/graphql"

        # Get times for both queries
        now = timezone.now()
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # GraphQL query for analytics data (both 15min and daily)
        query = """
        query {
          viewer {
            zones(filter: {zoneTag: "%s"}) {
              recent: httpRequestsAdaptiveGroups(
                filter: {
                  datetime_geq: "%s"
                  datetime_leq: "%s"
                  requestSource: "eyeball"
                }
                limit: 1000
              ) {
                count
                sum {
                  visits
                  edgeResponseBytes
                }
              }
              daily: httpRequestsAdaptiveGroups(
                filter: {
                  datetime_geq: "%s"
                  datetime_leq: "%s"
                  requestSource: "eyeball"
                }
                limit: 10000
              ) {
                count
                sum {
                  visits
                  edgeResponseBytes
                }
              }
            }
          }
        }
        """ % (
            settings.CLOUDFLARE_ZONE_ID,
            # Recent (15 minutes for active users)
            (now - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            # Daily (since midnight for total stats)
            start_of_today.strftime("%Y-%m-%dT%H:%M:%SZ"),
            now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        payload = {"query": query}

        response = requests.post(url, headers=headers, json=payload, timeout=3)

        if response.status_code == 200:
            data = response.json()

            if not data.get("errors"):
                zones = data.get("data", {}).get("viewer", {}).get("zones", [])
                if zones:
                    zone_data = zones[0]

                    # Recent data (last 15 minutes) for "active users"
                    recent_requests = zone_data.get("recent", [])
                    recent_visitors = 0
                    if recent_requests:
                        recent_visitors = sum(
                            group["sum"]["visits"] for group in recent_requests
                        )

                    # Daily data (since midnight) for "today's visits" and "unique visitors"
                    daily_requests = zone_data.get("daily", [])
                    daily_page_views = 0
                    daily_visitors = 0
                    if daily_requests:
                        daily_page_views = sum(
                            group["count"] for group in daily_requests
                        )
                        daily_visitors = sum(
                            group["sum"]["visits"] for group in daily_requests
                        )

                    return {
                        "active_users": recent_visitors,  # Last 15 min
                        "page_views": daily_page_views,  # Today's total
                        "unique_visitors": daily_visitors,  # Today's unique
                    }
            else:
                if settings.DEBUG:
                    raise Exception(
                        f"Cloudflare GraphQL errors: {data.get('errors', [])}"
                    )
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(f"Cloudflare GraphQL errors: {data.get('errors', [])}")
        else:
            if settings.DEBUG:
                raise Exception(
                    f"Cloudflare API request failed with status {response.status_code}"
                )
            else:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Cloudflare API request failed with status {response.status_code}"
                )

        if settings.DEBUG:
            raise Exception("Could not retrieve Cloudflare analytics data")
        return {"active_users": "?", "page_views": "?", "unique_visitors": "?"}

    except Exception as e:
        if settings.DEBUG:
            raise Exception(f"Cloudflare Analytics API error: {e}")
        else:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Cloudflare Analytics API error: {e}")
        return {"active_users": "?", "page_views": "?", "unique_visitors": "?"}


@csrf_exempt
@require_http_methods(["GET"])
@cache_page(30)  # Cache for 30 seconds
def live_status_view(request):
    """
    Live status using Cloudflare Analytics instead of custom tracking
    """
    # Get Cloudflare analytics data
    cf_analytics = get_cloudflare_analytics()

    # Get cached previous good values
    cached_stats = cache.get("cloudflare_last_good_stats", {})

    # For each stat, use new value if good, otherwise keep previous good value
    final_stats = {}
    for key in ["active_users", "page_views", "unique_visitors"]:
        new_value = cf_analytics.get(key, "?")
        old_value = cached_stats.get(key, "?")

        # If new value is good (not "?"), use it and cache it
        if new_value != "?" and new_value is not None:
            final_stats[key] = new_value
            cached_stats[key] = new_value
        else:
            # New value is bad, use old cached value if available
            if old_value != "?" and old_value is not None:
                final_stats[key] = old_value
                # Log when we go from good to bad values
                if old_value != "?" and new_value == "?":
                    logger.warning(
                        f"Cloudflare analytics for '{key}' returned '?' but using cached value: {old_value}"
                    )
            else:
                # No good value available at all
                final_stats[key] = "?"

    # Update cache with current good values (expires in 1 hour)
    if any(v != "?" for v in final_stats.values()):
        cache.set("cloudflare_last_good_stats", cached_stats, 3600)

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
    ko_fi_progress = get_ko_fi_progress()

    # Create response with low TTL headers to prevent Cloudflare caching
    response = JsonResponse(
        {
            "active_users": final_stats["active_users"],
            "page_views": final_stats["page_views"],
            "unique_visitors": final_stats["unique_visitors"],
            "server_offset": server_offset,
            "ko_fi_progress": ko_fi_progress,
            "timestamp": timezone.now().isoformat(),
            "cached": True,
            "source": "cloudflare_analytics",
        }
    )

    # Set low TTL headers to prevent Cloudflare caching
    response["Cache-Control"] = "public, max-age=30"
    response["Vary"] = "Cookie"
    response["Expires"] = (timezone.now() + timedelta(seconds=30)).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    return response
