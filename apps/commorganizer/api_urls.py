from django.urls import path
from . import views

app_name = "commorganizer_api"

urlpatterns = [
    path("new_comments/", views.api_new_comments, name="new_comments"),
]
