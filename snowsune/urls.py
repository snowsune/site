from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

from snowsune.views.home import HomeView
from snowsune.views.projects import ProjectsView
from snowsune.views.tools import ToolsView
from snowsune.views.live_status import live_status_view
from snowsune.views.image_utils import format_preview_view
from snowsune.views.randal_fanclub import RandalFanclubView
from apps.thank_yous.views import thank_you_view


urlpatterns = [
    # django
    path("admin/", admin.site.urls),
    # "local" urls
    path("", HomeView.as_view(), name="home"),
    path("projects/", ProjectsView.as_view(), name="projects"),
    path("tools/", ToolsView.as_view(), name="tools"),
    path("thank-you/", thank_you_view, name="thank_you"),
    path("login/", HomeView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # API endpoints
    path("api/live/", live_status_view, name="live_status_api"),
    path("api/quotes/", include("apps.quotes.api_urls")),
    path("api/commorganizer/", include("apps.commorganizer.api_urls")),
    # Image formatting for social media previews
    path(
        "format_preview/<path:image_path>", format_preview_view, name="format_preview"
    ),
    # "app" urls
    path("blog/", include("apps.blog.urls")),
    path("comics/", include("apps.comics.urls")),
    path("commorganizer/", include("apps.commorganizer.urls")),
    path("characters/", include("apps.characters.urls")),
    path("quotes/", include("apps.quotes.urls")),
    path("users/", include("apps.users.urls")),
    path("fops/", include("apps.bot_manager.urls")),
    path("bookclub/", include("apps.bookclub.urls")),
    # Hidden pages
    path("orfc/", RandalFanclubView.as_view(), name="randal_fanclub"),
    # SEO
    path(
        "sitemap.xml",
        lambda request: HttpResponse(
            open("static/sitemap.xml").read(), content_type="application/xml"
        ),
        name="sitemap",
    ),
    path(
        "robots.txt",
        lambda request: HttpResponse(
            open("robots.txt").read(), content_type="text/plain"
        ),
        name="robots",
    ),
]


# Extra/automated url patterns

# For Media (Serving static from whats in config)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
