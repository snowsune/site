from django.conf import settings
from django.http import HttpRequest, HttpResponseRedirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "HEAD"])
def matrix_redirect(_request: HttpRequest, *_args, **_kwargs):
    """
    /matrix* redirect to the Matrix join widget.
    """
    return HttpResponseRedirect(settings.MATRIX_WIDGET_URL)
