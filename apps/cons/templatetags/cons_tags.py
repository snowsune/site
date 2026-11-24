from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("cons/mff_countdown.html")
def mff_countdown(match="MFF", lookahead_days=14):
    """
    Homepage widget

    Usage: {% load cons_tags %}{% mff_countdown %}
    """
    return {
        "events_api_url": reverse("calendar_events_api"),
        "calendar_url": reverse("calendar"),
        "match": match,
        "lookahead_days": lookahead_days,
    }
