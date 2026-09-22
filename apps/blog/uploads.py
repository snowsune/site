"""
Blog editor RULES
..and things

idk i got tired of chasing constants >.<
"""

import hashlib
import html
import os
import re

from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.safestring import mark_safe
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

# Markdown-rendered <a href="/media/blog/...">label</a> download links.
_DOWNLOAD_LINK = re.compile(
    r'<a\s+href="(/media/(blog/(?:images|uploads)/[^"]+))"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
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


def file_sha256(file_obj):
    digest = hashlib.sha256()
    try:
        file_obj.open("rb")
    except Exception:
        pass
    try:
        try:
            file_obj.seek(0)
        except Exception:
            pass
        if hasattr(file_obj, "chunks"):
            for chunk in file_obj.chunks(1024 * 1024):
                digest.update(chunk)
        else:
            while True:
                chunk = file_obj.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    finally:
        try:
            file_obj.seek(0)
        except Exception:
            pass
    return digest.hexdigest()


def media_storage_path(href):
    """Turn /media/blog/uploads/x into blog/uploads/x."""
    media_url = settings.MEDIA_URL.rstrip("/") + "/"
    if href.startswith(media_url):
        return href[len(media_url) :]
    if href.startswith("/media/"):
        return href[len("/media/") :]
    return None


def download_card_html(upload, href, label):
    name = html.escape(upload.filename or label or os.path.basename(href))
    size = filesizeformat(upload.size) if upload.size else None
    checksum = upload.checksum or ""
    meta_bits = []
    if size:
        meta_bits.append(html.escape(str(size)))
    if checksum:
        meta_bits.append(
            f'<span class="blog-download-checksum" title="{html.escape(checksum)}">'
            f"SHA-256 {html.escape(checksum)}</span>"
        )
    meta_html = (
        f'<div class="blog-download-meta">{" · ".join(meta_bits)}</div>'
        if meta_bits
        else ""
    )
    return (
        f'<aside class="blog-download">'
        f'<a class="blog-download-name" href="{html.escape(href)}" download="{name}">'
        f"{name}</a>"
        f"{meta_html}"
        f"</aside>"
    )


def enhance_download_links(content_html):
    """Turn plain media download links into size/checksum cards."""
    if not content_html:
        return content_html

    # Local import: models import helpers from this module.
    from .models import BlogImage

    def replace(match):
        href, label = match.group(1), match.group(2)
        path = media_storage_path(href)
        if not path:
            return match.group(0)
        upload = BlogImage.objects.filter(image=path).first()
        if not upload or upload.is_image:
            return match.group(0)
        plain = re.sub(r"<[^>]+>", "", label or "").strip()
        return download_card_html(upload, href, plain)

    return mark_safe(_DOWNLOAD_LINK.sub(replace, content_html))
