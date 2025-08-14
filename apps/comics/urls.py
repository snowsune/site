from django.urls import path
from . import views

app_name = "comics"

urlpatterns = [
    path("", views.comic_home, name="comic_home"),
    path("page/<int:page_number>/", views.page_detail, name="page_detail"),
    path("page/<int:page_number>/nsfw/", views.nsfw_confirm, name="nsfw_confirm"),
    path("page/<int:page_number>/comment/", views.add_comment, name="add_comment"),
    path(
        "page/<int:page_number>/navigation/",
        views.page_navigation,
        name="page_navigation",
    ),
]
