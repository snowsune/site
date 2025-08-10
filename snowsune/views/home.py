from django.views import View
from django.shortcuts import render
from apps.blog.models import BlogPost


class HomeView(View):
    def get(self, request, *args, **kwargs):
        # Get the latest published blog post
        latest_post = (
            BlogPost.objects.filter(status="published")
            .order_by("-published_at", "-created_at")
            .first()
        )

        context = {"latest_post": latest_post}

        return render(request, "home.html", context)
