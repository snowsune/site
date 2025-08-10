from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from .models import BlogPost, Tag, BlogImage
from .forms import BlogPostForm, BlogPostCreateForm, TagForm


class BlogListView(ListView):
    model = BlogPost
    template_name = "blog/blog_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            BlogPost.objects.filter(status="published")
            .select_related("author")
            .prefetch_related("tags")
        )

        # Filter by tag if specified
        tag_slug = self.request.GET.get("tag")
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Search functionality
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all().order_by("name")
        context["recent_posts"] = BlogPost.objects.filter(status="published")[:5]
        return context


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = "blog/blog_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return BlogPost.objects.select_related("author").prefetch_related("tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_posts"] = (
            BlogPost.objects.filter(status="published", tags__in=self.object.tags.all())
            .exclude(id=self.object.id)
            .distinct()[:3]
        )
        return context


class BlogCreateView(LoginRequiredMixin, CreateView):
    model = BlogPost
    form_class = BlogPostCreateForm
    template_name = "blog/blog_form.html"
    success_url = reverse_lazy("blog:blog_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        messages.success(self.request, "Blog post created successfully!")
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class BlogUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = "blog/blog_form.html"

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Blog post updated successfully!")
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class BlogDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = BlogPost
    template_name = "blog/blog_confirm_delete.html"
    success_url = reverse_lazy("blog:blog_list")

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Blog post deleted successfully!")
        return super().delete(request, *args, **kwargs)


@login_required
def blog_dashboard(request):
    """Dashboard for managing blog posts"""
    user_posts = BlogPost.objects.filter(author=request.user).order_by("-updated_at")
    draft_posts = user_posts.filter(status="draft")
    published_posts = user_posts.filter(status="published")

    context = {
        "draft_posts": draft_posts,
        "published_posts": published_posts,
        "total_posts": user_posts.count(),
    }
    return render(request, "blog/blog_dashboard.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    """Handle image uploads for the blog editor"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        image_file = request.FILES.get("image")
        if not image_file:
            return JsonResponse({"error": "No image file provided"}, status=400)

        # Create BlogImage instance
        blog_image = BlogImage.objects.create(
            image=image_file, uploaded_by=request.user, filename=image_file.name
        )

        return JsonResponse(
            {
                "success": True,
                "url": blog_image.image.url,
                "markdown_link": blog_image.markdown_link,
                "filename": blog_image.filename,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


class BlogRSSFeed(Feed):
    title = "Snowsune Blog"
    link = "/blog/"
    description = "Latest blog posts from Snowsune"
    feed_type = Rss201rev2Feed

    def items(self):
        return BlogPost.objects.filter(status="published").order_by("-published_at")[
            :20
        ]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_link(self, item):
        return item.get_absolute_url()

    def item_author_name(self, item):
        return item.author.username

    def item_pubdate(self, item):
        return item.display_date

    def item_updateddate(self, item):
        return item.updated_at

    def item_categories(self, item):
        return [tag.name for tag in item.tags.all()]


def blog_landing(request):
    """Landing page for the blog"""
    latest_posts = (
        BlogPost.objects.filter(status="published")
        .select_related("author")
        .prefetch_related("tags")[:6]
    )
    popular_tags = Tag.objects.all()[:10]

    context = {
        "latest_posts": latest_posts,
        "popular_tags": popular_tags,
    }
    return render(request, "blog/landing.html", context)
