from django.urls import path
from . import views

app_name = "bookclub"

urlpatterns = [
    path("", views.bookclub_view, name="index"),
]
