from django.urls import path
from . import views

urlpatterns = [
    path("", views.commorganizer_landing, name="commorganizer"),
]
