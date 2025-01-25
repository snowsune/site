import os

from django.conf import settings


def version_processor(request):
    return {
        "version": os.getenv("GIT_COMMIT"),
    }
