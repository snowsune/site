from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """Simple health check endpoint that bypasses all middleware and context processors"""
    return HttpResponse("OK", content_type="text/plain", status=200)
