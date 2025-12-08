from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def process_spoilers(text):
    """
    Process spoilers marked with ||...|| and convert them to clickable spoiler tags.

    Usage: {{ comment|process_spoilers|linebreaks }}
    """
    if not text:
        return ""

    # Pattern to match ||...|| (non-greedy)
    pattern = r"\|\|(.*?)\|\|"

    def replace_spoiler(match):
        spoiler_content = match.group(1)
        return f'<span class="spoiler" onclick="this.classList.toggle(\'revealed\')">{spoiler_content}</span>'

    # Replace all spoiler markers
    processed = re.sub(pattern, replace_spoiler, text)
    return mark_safe(processed)
