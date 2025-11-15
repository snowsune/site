from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MonthlyComic, UserProgress


def bookclub_view(request):
    """Main bookclub page"""
    comic = MonthlyComic.objects.first()  # Get most recent

    if request.method == "POST" and request.user.is_authenticated:
        # Handle page number submission
        try:
            page_number = int(request.POST.get("page_number", 0))
            if comic and comic.start_page <= page_number <= comic.end_page:
                progress, created = UserProgress.objects.get_or_create(
                    user=request.user
                )
                progress.page_number = page_number
                progress.save()
                messages.success(request, "Progress updated!")
            elif comic:
                messages.error(
                    request,
                    f"Page number must be between {comic.start_page} and {comic.end_page}",
                )
            else:
                messages.error(
                    request, "No comic selected. Please set up a monthly comic first."
                )
        except ValueError:
            messages.error(request, "Invalid page number")
        return redirect("bookclub:index")

    # Calculate positions for leaderboard
    progress_list = []
    if comic:
        all_progress = UserProgress.objects.select_related("user").all()
        for progress in all_progress:
            position = progress.get_position_percentage(
                comic.start_page, comic.end_page
            )
            progress_list.append(
                {
                    "progress": progress,
                    "position": position,
                }
            )
        # Sort by page number (descending)
        progress_list.sort(key=lambda x: x["progress"].page_number, reverse=True)
        progress_list = progress_list[:10]  # Top 10

    user_progress = None
    user_position = None
    if request.user.is_authenticated:
        user_progress_obj = UserProgress.objects.filter(user=request.user).first()
        if user_progress_obj and comic:
            user_progress = user_progress_obj
            user_position = user_progress.get_position_percentage(
                comic.start_page, comic.end_page
            )

    context = {
        "comic": comic,
        "progress_list": progress_list,
        "user_progress": user_progress,
        "user_position": user_position,
    }
    return render(request, "bookclub/index.html", context)
