from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="bot_manager_dashboard"),
    path("redirect/", views.fops_redirect_view, name="bot_manager_redirect"),
    path("guild/<str:guild_id>/", views.guild_detail, name="bot_manager_guild"),
    path("table/<str:table_name>/", views.table_data, name="bot_manager_table"),
    path("discord/login/", views.discord_login, name="bot_manager_discord_login"),
    path(
        "discord/callback/", views.discord_callback, name="bot_manager_discord_callback"
    ),
    # Subscription management
    path(
        "subscriptions/add/",
        views.add_subscription,
        name="bot_manager_add_subscription",
    ),
    path(
        "subscriptions/add/<str:guild_id>/",
        views.add_subscription,
        name="bot_manager_add_subscription_for_guild",
    ),
    path(
        "subscriptions/<int:subscription_id>/edit/",
        views.edit_subscription,
        name="bot_manager_edit_subscription",
    ),
    path(
        "subscriptions/<int:subscription_id>/delete/",
        views.delete_subscription,
        name="bot_manager_delete_subscription",
    ),
]
