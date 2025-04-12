from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("register/", views.register_view, name="register"),
    path("edit/", views.edit_account_view, name="account-edit"),
    path("gallery/", views.user_gallery, name="user-gallery"),
]
