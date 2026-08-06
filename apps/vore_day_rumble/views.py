from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .bracket import build_bracketry_data
from .forms import ContestantEntryForm
from .models import Contestant, Match, RumbleSettings, reshuffle_bracket


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
    # Sweep any votes whose timer already elapsed
    from .voting.runner import resolve_due_votes

    try:
        resolve_due_votes()
    except Exception:
        pass

    settings = RumbleSettings.get()
    contestants = Contestant.objects.select_related("user").all()
    active_match = Match.objects.filter(voting_open=True).select_related(
        "contestant_a", "contestant_b"
    ).first()
    return render(
        request,
        "vore_day_rumble/index.html",
        {
            "settings": settings,
            "contestants": contestants,
            "active_match": active_match,
            "contestant_count": contestants.count(),
            "bracket_data": build_bracketry_data(),
        },
    )


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
            initial["display_name"] = (
                request.user.first_name or request.user.username
            )
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
