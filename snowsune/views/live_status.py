import requests
import json
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.conf import settings
from snowsune.models import SiteSetting


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
        if not settings.DEBUG:
            raise Exception("Cloudflare Analytics API is not configured")
        return {"active_users": "?", "page_views": "?", "unique_visitors": "?"}

    try:
        headers = {
            "Authorization": f"Bearer {settings.CLOUDFLARE_ANALYTICS_API_TOKEN}",
            "Content-Type": "application/json",
        }

        # Use GraphQL Analytics API
        url = "https://api.cloudflare.com/client/v4/graphql"

        # GraphQL query for analytics data
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
                limit: 1000
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
            (timezone.now() - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        payload = {"query": query}

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if not data.get("errors"):
                zones = data.get("data", {}).get("viewer", {}).get("zones", [])
                if zones:
                    zone_data = zones[0]
                    http_requests = zone_data.get("httpRequestsAdaptiveGroups", [])

                    if http_requests:
                        total_requests = sum(group["count"] for group in http_requests)
                        total_visits = sum(
                            group["sum"]["visits"] for group in http_requests
                        )

                        return {
                            "active_users": total_visits,
                            "page_views": total_requests,
                            "unique_visitors": total_visits,
                        }
            else:
                # Log GraphQL errors in production
                if not settings.DEBUG:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(f"Cloudflare GraphQL errors: {data.get('errors', [])}")
        else:
            # Log API errors in production
            if not settings.DEBUG:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Cloudflare API request failed with status {response.status_code}"
                )

        return {"active_users": "?", "page_views": "?", "unique_visitors": "?"}

    except Exception as e:
        # Log errors in production
        if not settings.DEBUG:
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

    return JsonResponse(
        {
            "active_users": cf_analytics["active_users"],
            "page_views": cf_analytics["page_views"],
            "unique_visitors": cf_analytics["unique_visitors"],
            "server_offset": server_offset,
            "ko_fi_progress": ko_fi_progress,
            "timestamp": timezone.now().isoformat(),
            "cached": True,
            "source": "cloudflare_analytics",
        }
    )
