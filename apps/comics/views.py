from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import ComicPage


def page_detail(request, page_number):
    """Display a specific comic page with navigation"""
    # Only allow access to published comics
    page = get_object_or_404(ComicPage.published, page_number=page_number)

    # Get latest pages for sidebar
    latest_pages = ComicPage.published.order_by("-page_number")[:10]

    # Check if this is the latest page
    latest_page = ComicPage.published.order_by("-page_number").first()

    context = {
        "page": page,
        "next_page": page.get_next_page(),
        "previous_page": page.get_previous_page(),
        "latest_pages": latest_pages,
        "latest_page": latest_page,
    }
    return render(request, "comics/page_detail.html", context)


def comic_home(request):
    """Redirect to the latest comic page"""
    latest_page = ComicPage.published.order_by("-page_number").first()
    if latest_page:
        return redirect("comics:page_detail", page_number=latest_page.page_number)
    else:
        # Catching if no comics exist, redirect to home page with a message
        from django.contrib import messages

        messages.warning(request, "No comic pages have been published yet.")
        return redirect("home")


def page_navigation(request, page_number):
    """AJAX endpoint for page navigation data"""
    # Only allow access to published comics
    page = get_object_or_404(ComicPage.published, page_number=page_number)

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
