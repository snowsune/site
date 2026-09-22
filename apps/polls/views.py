from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView

from apps.notifications.utils import (
    show_error_notification,
    show_success_notification,
)

from .forms import VoteForm
from .models import Poll, Vote


class OpenPollListView(ListView):
    model = Poll
    template_name = "polls/poll_list.html"
    context_object_name = "polls"

    def get_queryset(self):
        return Poll.objects.currently_open().prefetch_related("choices")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ended_count"] = Poll.objects.ended().count()
        return context


class PollArchiveView(ListView):
    model = Poll
    template_name = "polls/poll_archive.html"
    context_object_name = "polls"
    paginate_by = 12

    def get_queryset(self):
        return Poll.objects.ended().prefetch_related("choices")


class PollDetailView(DetailView):
    model = Poll
    template_name = "polls/poll_detail.html"
    context_object_name = "poll"

    def get_queryset(self):
        qs = Poll.objects.prefetch_related("choices")
        if self.request.user.is_staff:
            return qs
        return qs.visible()


@login_required
def vote(request, slug):
    poll = get_object_or_404(Poll.objects.prefetch_related("choices"), slug=slug)

    if request.method != "POST":
        return redirect(poll.get_absolute_url())

    if not poll.is_open:
        show_error_notification(request, "This poll is not open for voting.")
        return redirect(_next_url(request, poll))

    form = VoteForm(poll, request.POST)
    if not form.is_valid():
        errors = form.non_field_errors() or ["Could not save that vote."]
        show_error_notification(request, str(errors[0]))
        return redirect(_next_url(request, poll))

    choice_ids = form.cleaned_data["choice_ids"]
    with transaction.atomic():
        Vote.objects.filter(poll=poll, user=request.user).delete()
        Vote.objects.bulk_create(
            [
                Vote(poll=poll, user=request.user, choice_id=choice_id)
                for choice_id in choice_ids
            ]
        )

    show_success_notification(request, "Vote saved!")
    return redirect(_next_url(request, poll))


def _next_url(request, poll):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and nxt.startswith("/"):
        return nxt
    return poll.get_absolute_url()
