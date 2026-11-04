from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
from .models import MonthlyComic


class BookClubFeed(Feed):
    title = "Vixi's Webcomic Club!"
    link = "/bookclub/"
    description = "Monthly webcomic read-togethers at snowsune.net!"
    feed_type = Rss201rev2Feed

    def items(self):
        """Return all monthly comics ordered by most recent"""
        return MonthlyComic.objects.all().order_by("-updated_at")

    def item_title(self, item):
        """Return the title of each comic entry"""
        return f"Monthly Comic - {item.updated_at.date()}"

    def item_description(self, item):
        """Return the description/blurb of each comic"""
        if item.blurb_html:
            return item.blurb_html
        return item.blurb or "Monthly comic read"

    def item_link(self, item):
        """Return the URL for the bookclub page"""
        # Django's Feed class will automatically make this absolute
        return reverse("bookclub:index")

    def item_pubdate(self, item):
        """Return the publication date"""
        return item.updated_at

    def item_author_name(self, item):
        """Return the author name"""
        return "Snowsune Book Club"

    def item_categories(self, item):
        """Return categories for the comic"""
        return ["comics", "bookclub", "webcomics"]

    def item_enclosure_url(self, item):
        """Return the preview image URL if available"""
        if item.preview_image:
            return item.preview_image.url
        return None

    def item_enclosure_length(self, item):
        """Return the image file size if available"""
        if item.preview_image:
            try:
                return item.preview_image.size
            except:
                return 0
        return 0

    def item_enclosure_mime_type(self, item):
        """Return the image MIME type"""
        if item.preview_image:
            # Guess MIME type from file extension
            ext = item.preview_image.name.lower().split(".")[-1]
            mime_types = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "webp": "image/webp",
            }
            return mime_types.get(ext, "image/jpeg")
        return None
