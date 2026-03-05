from django.http import HttpResponse
from django.shortcuts import render

# Per-region reference link
REGION_451_REFERENCES = {
    "CA": (
        "https://www.eff.org/deeplinks/2024/02/eff-opposes-california-initiative-would-cause-mass-censorship",
        "EFF on CA AB 2273",
    )
}


class BlockGeoMiddleware:
    """Block geo with 451"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Normally CF dosn't pass these but, i have a catchall worker upstream (or it should be there)
        # Its passthru, and if no-match because i somehow exceed the limit then you just slip thru
        country = request.META.get("HTTP_X_CF_COUNTRY") or request.META.get(
            "HTTP_CF_IPCOUNTRY"
        )
        region = request.META.get("HTTP_X_CF_REGION")

        for blocked_region in REGION_451_REFERENCES:
            if region != blocked_region:
                continue
            ref = REGION_451_REFERENCES[blocked_region]
            ref_url, ref_text = ref if ref[0] else (None, None)
            context = {"reference_url": ref_url, "reference_text": ref_text}
            try:
                return render(request, "451.html", context, status=451)
            except Exception:
                fallback = "Unavailable for legal reasons in your region."
                if ref_url and ref_text:
                    fallback += (
                        f" See <a href='{ref_url}'>{ref_text}</a> for more information."
                    )
                return HttpResponse(fallback, status=451)

        return self.get_response(request)
