from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .bracket import build_bracketry_data
from .forms import ContestantEntryForm
from .models import Contestant, MatchVote, RumbleSettings, reshuffle_bracket
from .voting import live as vote_live


def rumble_enabled_required(view_func):
    """Off = come back next year page."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        settings = RumbleSettings.get()
        if not settings.enabled:
            return render(
                request,
                "vore_day_rumble/come_back.html",
                {"settings": settings},
            )
        return view_func(request, *args, **kwargs)

    return _wrapped


@rumble_enabled_required
def index(request):
    """Main rumble page."""
    from .voting.runner import resolve_due_votes

    try:
        resolve_due_votes()
    except Exception:
        pass

    settings = RumbleSettings.get()
    contestants = Contestant.objects.select_related("user").all()
    active_match = vote_live.active_match()
    vote_status = None
    if active_match and active_match.contestant_a and active_match.contestant_b:
        vote_status = vote_live.snapshot_for(request.user, active_match)

    return render(
        request,
        "vore_day_rumble/index.html",
        {
            "settings": settings,
            "contestants": contestants,
            "active_match": active_match,
            "vote_status": vote_status,
            "contestant_count": contestants.count(),
            "bracket_data": build_bracketry_data(),
        },
    )


@rumble_enabled_required
@require_GET
def vote_stream(request):
    """SSE status feed — tallies + this viewer's my_choice."""
    response = StreamingHttpResponse(
        vote_live.iter_sse(request.user),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache, no-store"
    response["X-Accel-Buffering"] = "no"
    return response


@rumble_enabled_required
@require_POST
def cast_vote(request):
    """Cast or switch your one vote for the current open match."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    choice = (request.POST.get("choice") or "").strip().lower()
    if choice not in (MatchVote.CHOICE_A, MatchVote.CHOICE_B):
        return JsonResponse({"error": "Invalid choice"}, status=400)

    match = vote_live.active_match()
    if match is None or not match.contestant_a or not match.contestant_b:
        return JsonResponse({"error": "No match is open for voting"}, status=400)

    if match.voting_ends_at and match.voting_ends_at <= timezone.now():
        from .voting.runner import resolve_vote

        try:
            resolve_vote(match)
        except Exception:
            pass
        return JsonResponse({"error": "Voting has closed"}, status=400)

    MatchVote.objects.update_or_create(
        match=match,
        user=request.user,
        defaults={"choice": choice},
    )
    vote_live.notify()
    response = JsonResponse(vote_live.snapshot_for(request.user, match))
    response["Cache-Control"] = "private, no-store"
    return response


@rumble_enabled_required
@login_required
def enter(request):
    """Sign up / update your entry."""
    settings = RumbleSettings.get()
    existing = Contestant.objects.filter(user=request.user).first()

    if not settings.signups_open and existing is None:
        return render(
            request,
            "vore_day_rumble/enter.html",
            {
                "settings": settings,
                "signups_closed": True,
                "existing": None,
                "form": None,
            },
        )

    if request.method == "POST":
        if not settings.signups_open:
            messages.error(request, "Signups are closed.")
            return redirect("vore_day_rumble:enter")

        form = ContestantEntryForm(
            request.POST,
            request.FILES,
            instance=existing,
        )
        if form.is_valid():
            contestant = form.save(commit=False)
            contestant.user = request.user
            contestant.save()
            if existing is None:
                reshuffle_bracket()
                messages.success(request, "You're in the rumble!")
            else:
                messages.success(request, "Entry updated!")
            return redirect("vore_day_rumble:enter")
    else:
        initial = {}
        if existing is None:
            initial["display_name"] = request.user.first_name or request.user.username
        form = ContestantEntryForm(instance=existing, initial=initial)

    return render(
        request,
        "vore_day_rumble/enter.html",
        {
            "settings": settings,
            "signups_closed": not settings.signups_open,
            "existing": existing,
            "form": form,
        },
    )
