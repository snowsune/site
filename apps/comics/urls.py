from django.urls import path
from . import views

app_name = "comics"

urlpatterns = [
    path("", views.comics_landing, name="landing"),
    path("browse/", views.webcomic_list, name="webcomic_list"),
    path("webcomic/<slug:slug>/", views.webcomic_detail, name="webcomic_detail"),
    path("subscribe/<int:webcomic_id>/", views.subscribe_to_webcomic, name="subscribe"),
    path(
        "unsubscribe/<int:webcomic_id>/",
        views.unsubscribe_from_webcomic,
        name="unsubscribe",
    ),
    path("my-subscriptions/", views.my_subscriptions, name="my_subscriptions"),
    path(
        "subscription/<int:subscription_id>/settings/",
        views.subscription_settings,
        name="subscription_settings",
    ),
    path("rss/<int:user_id>/", views.user_rss_feed, name="user_rss_feed"),
]
