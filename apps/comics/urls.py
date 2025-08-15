from django.urls import path
from . import views, feeds

app_name = "comics"

urlpatterns = [
    path("", views.comic_home, name="comic_home"),
    path("page/<int:page_number>/", views.page_detail, name="page_detail"),
    path(
        "page/<int:page_number>/navigation/",
        views.page_navigation,
        name="page_navigation",
    ),
    path("feed/", feeds.ComicsFeed(), name="comic_feed"),
]
