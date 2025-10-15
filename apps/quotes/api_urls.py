from django.urls import path
from . import views

app_name = "quotes_api"

urlpatterns = [
    path("", views.get_quotes, name="get_quotes"),
    path("webhook/", views.webhook_receive, name="webhook_receive"),
]
