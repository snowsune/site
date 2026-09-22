"""
Blog editor RULES
..and things

idk i got tired of chasing constants >.<
"""

import os

from django.conf import settings
from django.utils.text import get_valid_filename

# Executables, scripts, and markup that must not be served from /media/
DEFAULT_BLOCKED_UPLOAD_EXTENSIONS = frozenset(
    {
        ".html",
        ".htm",
        ".xhtml",
        ".svg",
        ".js",
        ".mjs",
        ".exe",
        ".dll",
        ".bat",
        ".cmd",
        ".sh",
        ".php",
    }
)

# Stuff to treat as inline images!
DEFAULT_IMAGE_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}
)


def blocked_upload_extensions():
    return getattr(
        settings,
        "BLOG_BLOCKED_UPLOAD_EXTENSIONS",
        DEFAULT_BLOCKED_UPLOAD_EXTENSIONS,
    )


def image_extensions():
    return getattr(settings, "BLOG_IMAGE_EXTENSIONS", DEFAULT_IMAGE_EXTENSIONS)


def clean_upload_filename(raw_name):
    base = get_valid_filename(os.path.basename(raw_name or "").replace("\x00", ""))
    root, ext = os.path.splitext(base)
    ext = ext.lower()
    if not root or not ext or ext in blocked_upload_extensions():
        return None
    if len(base) > 180:
        base = root[: 180 - len(ext)] + ext
    return base
