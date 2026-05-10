from django.urls import path

from . import views

app_name = "tanks_manager"

urlpatterns = [
    path("", views.tanks_root_redirect, name="root_redirect"),
    path("create/", views.create_my_tank, name="create"),
    path("<slug:slug>/edit/", views.edit, name="edit"),
    path("<slug:slug>/", views.tank_show, name="show"),
]
