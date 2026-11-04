"""
This started getting really complex so im breaking it out into samll files >.< website feels so big sometimes!

Each attachment put in a blogpost needs this bit to render it, theres a _attachment card html too as well
"""

import re

from django.template.loader import render_to_string

from .models import BlogImage

STANDALONE_LINK = re.compile(
    r"<p>\s*<a href=\"[^\"]*?/media/(?P<path>blog/(?:images|uploads)/[^\"]+)\"[^>]*>"
    r"(?P<label>.*?)</a>\s*</p>",
    re.DOTALL,
)


def render_attachments(html):
    if not html or "/media/blog/" not in html:
        return html

    paths = {m.group("path") for m in STANDALONE_LINK.finditer(html)}
    if not paths:
        return html

    uploads = {
        u.image.name: u
        for u in BlogImage.objects.filter(image__in=paths)
        if not u.is_image
    }
    if not uploads:
        return html

    def replace(match):
        upload = uploads.get(match.group("path"))
        if upload is None:
            return match.group(0)
        return render_to_string(
            "blog/_attachment_card.html",
            {"upload": upload, "label": match.group("label")},
        )

    return STANDALONE_LINK.sub(replace, html)
