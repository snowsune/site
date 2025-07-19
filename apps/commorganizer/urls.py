from django.urls import path
from . import views

urlpatterns = [
    path("", views.commorganizer_landing, name="commorganizer"),
    path(
        "manage/<str:commission_name>/",
        views.artist_dashboard,
        name="commorganizer-artist-dashboard",
    ),
    path(
        "<str:commission_name>/",
        views.public_commission_view,
        name="commorganizer-public-view",
    ),
    path(
        "api/new_comments/",
        views.api_new_comments,
        name="commorganizer-api-new-comments",
    ),
]
