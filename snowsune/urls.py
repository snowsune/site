from django.urls import path
from snowsune.views.home import HomeView
from snowsune.views.projects import ProjectsView
from snowsune.views.blog import BlogView
from snowsune.views.tools import ToolsView
from snowsune.views.comics import ComicsView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("projects/", ProjectsView.as_view(), name="projects"),
    path("blog/", BlogView.as_view(), name="blog"),
    path("tools/", ToolsView.as_view(), name="tools"),
    path("comics/", ComicsView.as_view(), name="comics"),
    path("login/", HomeView.as_view(), name="login"),
    path("logout/", HomeView.as_view(), name="logout"),
]
