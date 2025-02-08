import os

from django.conf import settings
from django.utils.safestring import mark_safe


# Returns the git version directly
def version_processor(request):
    return {
        "version": os.getenv("GIT_COMMIT"),
    }


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
