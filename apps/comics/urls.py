from django.urls import path
from . import views

urlpatterns = [
    path("", views.comics_landing, name="comics"),
]
