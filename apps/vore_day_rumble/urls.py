from django.urls import path

from . import views

app_name = "vore_day_rumble"

urlpatterns = [
    path("", views.index, name="index"),
    path("enter/", views.enter, name="enter"),
    path("vote/", views.cast_vote, name="cast_vote"),
    path("vote/stream/", views.vote_stream, name="vote_stream"),
]
