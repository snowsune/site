from django.urls import path

from . import views

app_name = "lists"

urlpatterns = [
    path("", views.lists_index, name="index"),
    path("<slug:list_slug>/", views.list_detail, name="list"),
    path("<slug:list_slug>/<slug:item_slug>/", views.item_detail, name="item"),
]
