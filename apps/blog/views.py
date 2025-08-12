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
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import BlogPost, Tag, BlogImage, Comment
from .forms import BlogPostForm, BlogPostCreateForm, TagForm, CommentForm


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

        # Get approved comments for this post
        comments = self.object.comments.filter(status="approved").select_related(
            "user", "parent"
        )

        # Organize comments into a tree structure
        comment_tree = self.build_comment_tree(comments)

        context["comments"] = comment_tree
        context["comment_form"] = CommentForm(
            user=self.request.user, post=self.object, request=self.request
        )
        context["related_posts"] = (
            BlogPost.objects.filter(status="published", tags__in=self.object.tags.all())
            .exclude(id=self.object.id)
            .distinct()[:3]
        )
        return context

    def build_comment_tree(self, comments):
        """Build a tree structure for threaded comments"""
        comment_dict = {}
        root_comments = []

        # First pass: create a dictionary of all comments
        for comment in comments:
            comment_dict[comment.id] = comment
            comment.replies_list = []

        # Second pass: build the tree
        for comment in comments:
            if comment.parent:
                # This is a reply
                if comment.parent.id in comment_dict:
                    comment_dict[comment.parent.id].replies_list.append(comment)
            else:
                # This is a root comment
                root_comments.append(comment)

        return root_comments


@require_POST
def submit_comment(request, post_id):
    """Handle comment submission"""
    post = get_object_or_404(BlogPost, id=post_id)

    # Check if comments are allowed (you could add a field to BlogPost for this)
    if post.status != "published":
        messages.error(request, "Comments are only allowed on published posts.")
        return redirect(post.get_absolute_url())

    form = CommentForm(request.POST, user=request.user, post=post, request=request)

    if form.is_valid():
        comment = form.save()

        if request.user.is_authenticated:
            messages.success(request, "Your comment has been posted successfully!")
        else:
            messages.success(
                request, "Your comment has been submitted and is awaiting moderation."
            )

        return redirect(post.get_absolute_url())
    else:
        # Store form errors in messages with better context
        if form.errors:
            messages.error(
                request,
                "There were issues with your comment submission. Please review the errors below.",
            )

            # Add specific field errors
            for field, errors in form.errors.items():
                field_name = field.replace("_", " ").title()
                for error in errors:
                    if field == "content":
                        messages.error(request, f"Comment: {error}")
                    elif field == "author_name":
                        messages.error(request, f"Name: {error}")
                    elif field == "author_email":
                        messages.error(request, f"Email: {error}")
                    elif field == "author_website":
                        messages.error(request, f"Website: {error}")
                    else:
                        messages.error(request, f"{field_name}: {error}")
        else:
            messages.error(request, "An unexpected error occurred. Please try again.")

    return redirect(post.get_absolute_url())


@login_required
def moderate_comment(request, comment_id, action):
    """Moderate a comment (approve, reject, mark as spam)"""
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if user has permission to moderate
    if not (request.user.is_staff or request.user == comment.post.author):
        messages.error(request, "You don't have permission to moderate comments.")
        return redirect(comment.post.get_absolute_url())

    if action == "approve":
        comment.status = "approved"
        messages.success(request, "Comment approved.")
    elif action == "reject":
        comment.status = "rejected"
        messages.success(request, "Comment rejected.")
    elif action == "spam":
        comment.status = "spam"
        messages.success(request, "Comment marked as spam.")
    else:
        messages.error(request, "Invalid moderation action.")
        return redirect(comment.post.get_absolute_url())

    comment.moderated_by = request.user
    comment.moderated_at = timezone.now()
    comment.save()

    return redirect(comment.post.get_absolute_url())


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

    # Get unapproved comments for posts authored by this user
    unapproved_comments = (
        Comment.objects.filter(post__author=request.user, status="pending")
        .select_related("post", "user")
        .order_by("-created_at")
    )

    # Get rejected and spam comments for transparency
    rejected_comments = (
        Comment.objects.filter(post__author=request.user, status="rejected")
        .select_related("post", "user")
        .order_by("-created_at")[:5]
    )

    spam_comments = (
        Comment.objects.filter(post__author=request.user, status="spam")
        .select_related("post", "user")
        .order_by("-created_at")[:5]
    )

    # Get total comment counts for better context
    total_comments = Comment.objects.filter(post__author=request.user).count()
    approved_comments = Comment.objects.filter(
        post__author=request.user, status="approved"
    ).count()

    context = {
        "draft_posts": draft_posts,
        "published_posts": published_posts,
        "total_posts": user_posts.count(),
        "unapproved_comments": unapproved_comments,
        "rejected_comments": rejected_comments,
        "spam_comments": spam_comments,
        "pending_comment_count": unapproved_comments.count(),
        "total_comment_count": total_comments,
        "approved_comment_count": approved_comments,
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
    description = "Snowsune.net RSS blog feed."
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
