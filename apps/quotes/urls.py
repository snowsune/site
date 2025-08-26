from django.urls import path
from . import views

app_name = "quotes"

urlpatterns = [
    path("webhook/", views.webhook_receive, name="webhook_receive"),
    path("api/quotes/", views.get_quotes, name="get_quotes"),
]
