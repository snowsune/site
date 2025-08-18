from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
from .models import ComicPage


class ComicsFeed(Feed):
    title = "Snowsune Comics"
    link = "/comics/"
    description = "Latest comics from Snowsune.net"
    feed_type = Rss201rev2Feed

    def items(self):
        """Return the latest 20 published comic pages"""
        return ComicPage.published.order_by("-published_at")[:20]

    def item_title(self, item):
        """Return the title of each comic page"""
        return f"Comic #{item.page_number}: {item.title}"

    def item_description(self, item):
        """Return the description of each comic page"""
        if item.description_html:
            return item.description_html
        return f"Comic #{item.page_number} - {item.title}"

    def item_link(self, item):
        """Return the URL for each comic page"""
        return item.get_absolute_url()

    def item_pubdate(self, item):
        """Return the publication date"""
        return item.published_at

    def item_updateddate(self, item):
        """Return the last updated date"""
        return item.updated_at

    def item_author_name(self, item):
        """Return the author name"""
        return "Vixi"

    def item_author_email(self, item):
        """Return the author email"""
        return "vixi@snowsune.net"

    def item_categories(self, item):
        """Return categories/tags for the comic"""
        return ["comics", "furry", "art"]

    def item_enclosure_url(self, item):
        """Return the comic image URL if available"""
        if item.image:
            return item.image.url
        return None

    def item_enclosure_length(self, item):
        """Return the image file size if available"""
        if item.image:
            try:
                return item.image.size
            except:
                return 0
        return 0

    def item_enclosure_mime_type(self, item):
        """Return the image MIME type"""
        if item.image:
            return "image/png"  # Adjust based on your image format
        return None
