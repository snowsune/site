from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="bot_manager_dashboard"),
    path("table/<str:table_name>/", views.table_data, name="bot_manager_table"),
    path("discord/login/", views.discord_login, name="bot_manager_discord_login"),
    path(
        "discord/callback/", views.discord_callback, name="bot_manager_discord_callback"
    ),
]
