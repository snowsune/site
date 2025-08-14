from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import ComicPage, ComicComment


def page_detail(request, page_number):
    """Display a specific comic page with navigation"""
    page = get_object_or_404(ComicPage, page_number=page_number)

    context = {
        "page": page,
        "next_page": page.get_next_page(),
        "previous_page": page.get_previous_page(),
        "comments": page.comments.filter(status="approved").order_by("created_at"),
    }
    return render(request, "comics/page_detail.html", context)


def comic_home(request):
    """Display the comic home page with latest pages"""
    latest_pages = ComicPage.objects.filter(published_at__isnull=False).order_by(
        "-page_number"
    )[:10]

    context = {
        "latest_pages": latest_pages,
        "total_pages": ComicPage.objects.filter(published_at__isnull=False).count(),
    }
    return render(request, "comics/comic_home.html", context)


@require_http_methods(["POST"])
def add_comment(request, page_number):
    """Add a comment to a comic page via AJAX"""
    page = get_object_or_404(ComicPage, page_number=page_number)

    if request.user.is_authenticated:
        author_name = request.user.username
        user = request.user
    else:
        author_name = request.POST.get("author_name", "")
        user = None

    content = request.POST.get("content", "")

    if not content or not author_name:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    comment = ComicComment.objects.create(
        page=page,
        author_name=author_name,
        content=content,
        user=user,
        status="pending",  # Requires moderation
    )

    return JsonResponse(
        {
            "success": True,
            "comment_id": comment.id,
            "message": "Comment submitted for moderation",
        }
    )


def page_navigation(request, page_number):
    """AJAX endpoint for page navigation data"""
    page = get_object_or_404(ComicPage, page_number=page_number)

    next_page = page.get_next_page()
    previous_page = page.get_previous_page()

    return JsonResponse(
        {
            "current_page": page_number,
            "has_next": page.has_next,
            "has_previous": page.has_previous,
            "next_page": next_page.page_number if next_page else None,
            "previous_page": previous_page.page_number if previous_page else None,
        }
    )
