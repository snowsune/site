from django.views import View
from django.shortcuts import render
from apps.blog.models import BlogPost


class HomeView(View):
    def get(self, request, *args, **kwargs):
        # Get the six latest published blog posts
        latest_posts = (
            BlogPost.objects.filter(status="published")
            .order_by("-published_at", "-created_at")
            .select_related("author")
            .prefetch_related("tags")[:6]
        )

        context = {"latest_posts": latest_posts}

        return render(request, "home.html", context)
