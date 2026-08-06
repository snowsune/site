from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .bracket import build_bracketry_data
from .forms import ContestantEntryForm
from .models import Contestant, Match, MatchVote, RumbleSettings, reshuffle_bracket


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


def _vote_payload(match, user=None):
    """JSON-friendly status for the live voting panel."""
    left, right = match.live_vote_counts()
    my_choice = None
    if user is not None and user.is_authenticated:
        vote = MatchVote.objects.filter(match=match, user=user).first()
        if vote:
            my_choice = vote.choice

    ends_at = match.voting_ends_at
    return {
        "match_id": match.pk,
        "voting_open": match.voting_open,
        "votes_left": left,
        "votes_right": right,
        "my_choice": my_choice,
        "ends_at": ends_at.isoformat() if ends_at else None,
        "ends_at_unix": int(ends_at.timestamp()) if ends_at else None,
        "server_now_unix": int(timezone.now().timestamp()),
        "name_a": match.contestant_a.display_name if match.contestant_a else None,
        "name_b": match.contestant_b.display_name if match.contestant_b else None,
    }


@rumble_enabled_required
def index(request):
    """Main rumble page."""
    # Sweep any votes whose timer already elapsed
    from .voting.runner import resolve_due_votes

    try:
        resolve_due_votes()
    except Exception:
        pass

    settings = RumbleSettings.get()
    contestants = Contestant.objects.select_related("user").all()
    active_match = (
        Match.objects.filter(voting_open=True)
        .select_related("contestant_a", "contestant_b")
        .first()
    )

    vote_status = None
    if active_match and active_match.contestant_a and active_match.contestant_b:
        vote_status = _vote_payload(active_match, request.user)

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
def vote_status(request):
    """Live tallies + countdown for the open match (poll this)."""
    match = (
        Match.objects.filter(voting_open=True)
        .select_related("contestant_a", "contestant_b")
        .first()
    )
    if match is None:
        return JsonResponse({"voting_open": False})
    return JsonResponse(_vote_payload(match, request.user))


@rumble_enabled_required
@require_POST
def cast_vote(request):
    """Cast or switch your one vote for the current open match."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    choice = (request.POST.get("choice") or "").strip().lower()
    if choice not in (MatchVote.CHOICE_A, MatchVote.CHOICE_B):
        return JsonResponse({"error": "Invalid choice"}, status=400)

    match = (
        Match.objects.filter(voting_open=True)
        .select_related("contestant_a", "contestant_b")
        .first()
    )
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
    return JsonResponse(_vote_payload(match, request.user))


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
            # New signup? reshuffle. Just an update? leave the bracket alone.
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
