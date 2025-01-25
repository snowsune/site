import os

from django.conf import settings


def version_processor(request):
    return {
        "version": os.getenv("GIT_COMMIT"),
    }


def debug_mode(request):
    return {
        "debug": settings.DEBUG,
    }
