from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

from snowsune.views.home import HomeView
from snowsune.views.projects import ProjectsView
from snowsune.views.tools import ToolsView
from snowsune.views.active_users import active_users_view
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
    path("logout/", HomeView.as_view(), name="logout"),
    # API endpoints
    path("api/active-users/", active_users_view, name="active_users_api"),
    # "app" urls
    path("blog/", include("apps.blog.urls")),
    path("comics/", include("apps.comics.urls")),
    path("commorganizer/", include("apps.commorganizer.urls")),
    path("characters/", include("apps.characters.urls")),
    path("users/", include("apps.users.urls")),
    path("", include("apps.pages.urls")),
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
