from django.urls import path
from . import views

urlpatterns = [
    path("", views.commorganizer_landing, name="commorganizer"),
    path(
        "my-commissions/",
        views.user_commission_select,
        name="commorganizer-user-select",
    ),
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
]
