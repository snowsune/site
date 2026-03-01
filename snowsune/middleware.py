from django.http import HttpResponse
from django.shortcuts import render


class BlockUKMiddleware:
    """Return 451"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        country = request.META.get("HTTP_CF_IPCOUNTRY")
        if country == "GB":
            try:
                return render(request, "451.html", {}, status=451)
            except Exception:
                return HttpResponse(
                    "Unavailable for legal reasons in your region.",
                    status=451,
                )
        return self.get_response(request)
