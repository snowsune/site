from django.urls import path
from . import views

app_name = "custompages"

urlpatterns = [
    path("<slug:path>", views.CustomPageDetailView.as_view(), name="page_detail"),
]
