from django.urls import path
from . import views

urlpatterns = [
    path("", views.character_list, name="character-list"),  # List all characters
    path(
        "<str:char_name>/", views.character_detail, name="character-detail"
    ),  # Single character page
]
