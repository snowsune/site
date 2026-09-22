from django import template

from ..forms import VoteForm

register = template.Library()


@register.inclusion_tag("polls/includes/poll_widget.html", takes_context=True)
def poll_widget(context, poll, compact=False):
    """Render a vote form and/or results for a poll."""
    request = context.get("request")
    user = getattr(request, "user", None)
    selected_ids = poll.user_choice_ids(user) if poll else []
    show_results = bool(poll) and (
        poll.has_ended
        or bool(selected_ids)
        or (user and user.is_authenticated and user.is_staff)
    )
    form = None
    if poll and poll.is_open:
        initial = {}
        if poll.choice_type == poll.CHOICE_SINGLE and selected_ids:
            initial["choice"] = selected_ids[0]
        elif selected_ids:
            initial["choices"] = [str(pk) for pk in selected_ids]
        form = VoteForm(poll, initial=initial)

    return {
        "poll": poll,
        "request": request,
        "user": user,
        "form": form,
        "choices": list(poll.choices.all()) if poll else [],
        "selected_ids": selected_ids,
        "show_results": show_results,
        "results": poll.results() if poll and show_results else [],
        "compact": compact,
        "voter_count": poll.voter_count() if poll else 0,
        "include_discord": bool(poll and poll.has_ended),
    }
