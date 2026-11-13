import logging
from datetime import timedelta

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


@csrf_exempt
@require_http_methods(["GET"])
@cache_page(30)
def live_status_view(request):
    active_users = get_active_logged_in_session_count()
    ko_fi_progress = get_ko_fi_progress()

    response = JsonResponse(
        {
            "active_users": active_users,
            "ko_fi_progress": ko_fi_progress,
            "timestamp": timezone.now().isoformat(),
        }
    )
    response["Cache-Control"] = "public, max-age=30"
    response["Vary"] = "Cookie"
    response["Expires"] = (timezone.now() + timedelta(seconds=30)).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    return response
