from django.urls import path

from . import views

app_name = "polls"

urlpatterns = [
    path("", views.OpenPollListView.as_view(), name="list"),
    path("archive/", views.PollArchiveView.as_view(), name="archive"),
    path("<slug:slug>/", views.PollDetailView.as_view(), name="detail"),
    path("<slug:slug>/vote/", views.vote, name="vote"),
]
