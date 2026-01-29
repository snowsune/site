import os

from django.http import HttpRequest, HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from snowsune.models import SiteSetting


@require_http_methods(["GET", "HEAD"])
def discord_redirect(_request: HttpRequest, *_args, **_kwargs):
    """
    Simple /discord* redirect.

    Returns an HTTP 302 to discord invite url
    """
    target = ""

    try:
        value = (
            SiteSetting.objects.filter(key="discord_invite")
            .values_list("value", flat=True)
            .first()
        )
        if value:
            target = value.strip()
    except Exception:
        target = "https://snowsune.net/discord_404".strip()

    return HttpResponseRedirect(target)

