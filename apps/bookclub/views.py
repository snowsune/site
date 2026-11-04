from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import MonthlyComic, UserProgress, Comment


def bookclub_view(request):
    """Main bookclub page"""
    comic = MonthlyComic.objects.first()  # Get most recent

    if request.method == "POST" and request.user.is_authenticated:
        # Handle page number submission
        try:
            page_number = int(request.POST.get("page_number", 0))
            comment = request.POST.get("comment", "").strip()
            if comic and comic.start_page <= page_number <= comic.end_page:
                progress, created = UserProgress.objects.get_or_create(
                    comic=comic, user=request.user
                )
                progress.page_number = page_number
                progress.comment = comment
                progress.save()

                # Create a new comment entry if comment is provided
                if comment:
                    Comment.objects.create(
                        comic=comic,
                        user=request.user,
                        page_number=page_number,
                        comment=comment,
                    )

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
        all_progress = UserProgress.objects.select_related("user").filter(comic=comic)
        for progress in all_progress:
            position = progress.get_position_percentage(
                comic.start_page, comic.end_page
            )
            formatted_date = (
                comic.format_page_as_readable_date(progress.page_number)
                if comic.use_date_format
                else None
            )
            progress_list.append(
                {
                    "progress": progress,
                    "position": position,
                    "formatted_date": formatted_date,
                }
            )
        # Sort by page number (descending)
        progress_list.sort(key=lambda x: x["progress"].page_number, reverse=True)
        progress_list = progress_list[:10]  # Top 10

    user_progress = None
    user_position = None
    if request.user.is_authenticated:
        user_progress_obj = UserProgress.objects.filter(
            comic=comic, user=request.user
        ).first()
        if user_progress_obj and comic:
            user_progress = user_progress_obj
            user_position = user_progress.get_position_percentage(
                comic.start_page, comic.end_page
            )

    # Get all comments (from Comment model - shows history for this comic)
    comments = []
    if comic:
        comments_queryset = (
            Comment.objects.select_related("user")
            .filter(comic=comic)
            .order_by("-created_at")
        )
        # Add formatted page URLs to each comment
        for comment_obj in comments_queryset:
            page_url = comic.get_page_url(comment_obj.page_number) if comic else None
            comments.append(
                {
                    "comment": comment_obj,
                    "page_url": page_url,
                }
            )

    # Format start/end dates if using date format
    comic_start_date = None
    comic_end_date = None
    if comic and comic.use_date_format:
        comic_start_date = comic.format_page_as_readable_date(comic.start_page)
        comic_end_date = comic.format_page_as_readable_date(comic.end_page)

    context = {
        "comic": comic,
        "progress_list": progress_list,
        "user_progress": user_progress,
        "user_position": user_position,
        "comments": comments,
        "comic_start_date": comic_start_date,
        "comic_end_date": comic_end_date,
    }
    return render(request, "bookclub/index.html", context)


@login_required
def delete_comment(request, comment_id):
    """Delete a comment - users can only delete their own comments"""
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if the user owns this comment
    if comment.user != request.user:
        return HttpResponseForbidden("You can only delete your own comments.")

    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted!")
        return redirect("bookclub:index")

    return redirect("bookclub:index")
