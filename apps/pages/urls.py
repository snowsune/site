from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path(
        "hungerfight/",
        views.PageDetailView.as_view(),
        {"slug": "hungerfight"},
        name="hungerfight",
    ),
    path(
        "hungerfight/edit/",
        views.PageEditView.as_view(),
        {"slug": "hungerfight"},
        name="hungerfight-edit",
    ),
]
