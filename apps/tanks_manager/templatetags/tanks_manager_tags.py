import re

from django import template

register = template.Library()

_HEX6 = re.compile(r"^[0-9a-fA-F]{6}$")


@register.filter
def hex_for_color_input(value):
    """Normalize stored color to #rrggbb for HTML color inputs."""
    if value is None:
        return "#ffffff"
    s = str(value).strip()
    if not s:
        return "#ffffff"
    if s.startswith("#"):
        s = s[1:]
    if len(s) == 3 and all(c in "0123456789abcdefABCDEF" for c in s):
        return "#" + "".join((c * 2) for c in s).lower()
    if len(s) == 6 and _HEX6.match(s):
        return "#" + s.lower()
    return "#ffffff"
