from django import template
from django.urls import reverse
from apps.comics.models import ComicPage

register = template.Library()


@register.inclusion_tag("comics/comic_frame.html")
def comic_frame(
    page_number=None, size="medium", show_description=True, show_navigation=True
):
    """
    Render a comic frame that can be used on any page.

    Usage:
    {% load comic_tags %}
    {% comic_frame page_number=1 size='small' show_description=False %}

    Parameters:
    - page_number: The page number to display (defaults to latest)
    - size: 'small', 'medium', 'large' (affects CSS classes)
    - show_description: Whether to show the comic description
    - show_navigation: Whether to show navigation controls
    """

    if page_number:
        try:
            current_page = ComicPage.objects.get(page_number=page_number)
        except ComicPage.DoesNotExist:
            current_page = None
    else:
        # Get the latest published page
        current_page = (
            ComicPage.objects.filter(published_at__isnull=False)
            .order_by("-page_number")
            .first()
        )

    # Get all available pages for the dropdown
    available_pages = ComicPage.objects.filter(published_at__isnull=False).order_by(
        "page_number"
    )

    return {
        "current_page": current_page,
        "available_pages": available_pages,
        "size": size,
        "show_description": show_description,
        "show_navigation": show_navigation,
    }


@register.simple_tag
def latest_comic_page():
    """Get the latest published comic page"""
    return (
        ComicPage.objects.filter(published_at__isnull=False)
        .order_by("-page_number")
        .first()
    )
