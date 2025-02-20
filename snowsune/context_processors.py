import os

from django.conf import settings
from django.utils.safestring import mark_safe

from datetime import datetime

from tracking.models import Visitor


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

    total_visits = Visitor.objects.count()  # Total visits recorded
    unique_visitors = (
        Visitor.objects.values("ip_address").distinct().count()
    )  # Unique IPs

    return {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
    }
