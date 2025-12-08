from django.urls import path
from . import views

app_name = "bookclub"

urlpatterns = [
    path("", views.bookclub_view, name="index"),
    path("comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
]
