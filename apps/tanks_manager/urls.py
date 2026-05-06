from django.urls import path

from . import views

app_name = "tanks_manager"

urlpatterns = [
    path("data.json", views.data_json, name="data_json"),
    path("", views.edit, name="edit"),
]
