from django.contrib import admin
from django.urls import path, include

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
]
