from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from snowsune.views.home import HomeView
from snowsune.views.projects import ProjectsView
from snowsune.views.tools import ToolsView


urlpatterns = [
    # django
    path("admin/", admin.site.urls),
    # "local" urls
    path("", HomeView.as_view(), name="home"),
    path("projects/", ProjectsView.as_view(), name="projects"),
    path("tools/", ToolsView.as_view(), name="tools"),
    path("login/", HomeView.as_view(), name="login"),
    path("logout/", HomeView.as_view(), name="logout"),
    # "app" urls
    path("blog/", include("apps.blog.urls")),
    path("comics/", include("apps.comics.urls")),
    path("characters/", include("apps.characters.urls")),
    path("users/", include("apps.users.urls")),
    path("", include("apps.pages.urls")),
]


# Extra/automated url patterns

# For Media (Serving static from whats in config)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
