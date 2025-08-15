import os

from django.conf import settings
from django.utils.safestring import mark_safe

from datetime import datetime, timezone
from django.utils import timezone as django_timezone

from tracking.models import Visitor
from .models import SiteSetting


# Returns the git version directly
def version_processor(request):
    return {
        "version": os.getenv("GIT_COMMIT"),
    }


# Processor for the current year
def year_processor(request):
    return {"year": datetime.now().year}


# True if we're in debug or not!
def debug_mode(request):
    return {
        "debug": settings.DEBUG,
    }


# Expiry links
def expiry_links(request):
    return {
        "discord": mark_safe(
            f"<a href=\"{os.getenv('DISCORD_URL','#')}\">Discord Server</a>"
        ),
    }


# Visitor/site stats
def visit_stats(request):
    """
    Just because I want to have these stats on every page
    """

    # Get today's date in the site's timezone
    today = django_timezone.now().date()

    # Get today's visits
    today_visits = Visitor.objects.filter(start_time__date=today).count()

    # Get today's unique visitors (by IP)
    today_unique_visitors = (
        Visitor.objects.filter(start_time__date=today)
        .values("ip_address")
        .distinct()
        .count()
    )

    return {
        "today_visits": today_visits,
        "today_unique_visitors": today_unique_visitors,
    }


# Quick processor for the discord invite link
# TODO: Could be made generic for all SiteSettings
def discord_invite_link(request):
    invite = SiteSetting.objects.filter(key="discord_invite").first()
    return {"discord_invite": invite.value if invite else ""}
