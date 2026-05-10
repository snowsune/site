from django.urls import path

from . import views

app_name = "tanks_manager"

urlpatterns = [
    path("", views.tanks_hub, name="hub"),
    path("create/", views.create_my_tank, name="create"),
    path("<slug:slug>/delete/", views.delete_my_tank, name="delete"),
    path("<slug:slug>/edit/", views.edit, name="edit"),
    path("<slug:slug>/", views.tank_show, name="show"),
]
