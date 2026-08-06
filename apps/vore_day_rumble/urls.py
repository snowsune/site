from django.urls import path

from . import views

app_name = "vore_day_rumble"

urlpatterns = [
    path("", views.index, name="index"),
    path("enter/", views.enter, name="enter"),
]
