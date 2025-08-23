from django import template
from ..views.image_utils import get_social_preview_url

register = template.Library()


@register.filter
def social_preview_url(image_url):
    """
    Convert a regular image URL to a social preview URL.

    Usage: {{ post.featured_image.url|social_preview_url }}
    """
    return get_social_preview_url(image_url)


@register.filter
def social_preview_url_og(image_url, request=None):
    """
    Convert a regular image URL to a social preview URL for Open Graph.
    Returns the full URL including domain.

    Usage: {{ post.featured_image.url|social_preview_url_og:request }}
    """
    if not image_url:
        return None

    preview_path = get_social_preview_url(image_url)
    if preview_path:
        if request:
            # Use the current request's domain
            return f"{request.scheme}://{request.get_host()}{preview_path}"
        else:
            # Fallback to hardcoded domain
            return f"https://snowsune.net{preview_path}"
    return None
