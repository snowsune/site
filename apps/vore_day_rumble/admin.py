from django.contrib import admin, messages
from django.db.models import Q

from .models import (
    Contestant,
    Match,
    MatchVote,
    RumbleSettings,
    apply_match_forfeit,
    open_next_match_for_voting,
    winner_if_withdrawal,
)


@admin.register(RumbleSettings)
class RumbleSettingsAdmin(admin.ModelAdmin):
    list_display = ["__str__", "enabled", "signups_open", "discord_channel_id"]
    fieldsets = (
        (
            "Toggles",
            {
                "fields": (
                    "enabled",
                    "signups_open",
                    "advance_to_next_match",
                    "reset_bracket",
                ),
                "description": (
                    "enabled = site is live, signups_open = /voreday/enter works, "
                    "advance_to_next_match = open the next match for site voting "
                    "(Discord still announces), "
                    "reset_bracket = wipe + reshuffle (keeps contestants)."
                ),
            },
        ),
        (
            "Discord + voting window",
            {
                "fields": ("discord_channel_id", "vote_duration_minutes"),
                "description": (
                    "Votes are cast on snowsune.net. Discord gets the matchup image, "
                    "countdown, and results. Needs DISCORD_BOT_TOKEN; bot must post "
                    "images/text in this channel. Votes auto-close on a timer; "
                    "/voreday/ also sweeps due ones."
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return not RumbleSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = [
        "display_name",
        "user",
        "bracket_position",
        "withdrawn",
        "has_pfp",
        "created_at",
    ]
    list_filter = ["withdrawn", "created_at"]
    search_fields = ["display_name", "user__username"]
    readonly_fields = ["bracket_position", "created_at", "updated_at"]
    autocomplete_fields = ["user"]
    ordering = ["bracket_position"]
    actions = ["mark_withdrawn", "clear_withdrawn", "kick_from_rumble"]

    @admin.display(boolean=True, description="Has PFP")
    def has_pfp(self, obj):
        return bool(obj.profile_picture)

    @admin.action(description="Mark withdrawn (keep bracket, auto-forfeit upcoming)")
    def mark_withdrawn(self, request, queryset):
        ids = list(queryset.values_list("pk", flat=True))
        n = Contestant.objects.filter(pk__in=ids).update(withdrawn=True)
        forfeited = 0
        open_matches = (
            Match.objects.select_related("contestant_a", "contestant_b")
            .filter(voting_open=True)
            .filter(Q(contestant_a_id__in=ids) | Q(contestant_b_id__in=ids))
        )
        for match in open_matches:
            winner = winner_if_withdrawal(match)
            if winner is None:
                continue
            apply_match_forfeit(match, winner)
            forfeited += 1
            from .voting.live import notify as notify_vote_live

            notify_vote_live()
        self.message_user(
            request,
            f"Marked {n} withdrawn. Closed {forfeited} open match(es) via forfeit. "
            "Bracket otherwise unchanged — they'll auto-lose when their next match is claimed.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Clear withdrawn (they can play again)")
    def clear_withdrawn(self, request, queryset):
        n = queryset.update(withdrawn=False)
        self.message_user(
            request,
            f"Cleared withdrawn on {n} contestant(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Kick from rumble (delete + reshuffle bracket)")
    def kick_from_rumble(self, request, queryset):
        from .models import reshuffle_bracket

        names = list(queryset.values_list("display_name", flat=True))
        n = queryset.count()
        queryset.delete()
        reshuffle_bracket()
        who = ", ".join(names[:8])
        if len(names) > 8:
            who += f", +{len(names) - 8} more"
        self.message_user(
            request,
            f"Kicked {n}: {who}. Bracket reshuffled.",
            level=messages.SUCCESS,
        )


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "round_number",
        "position",
        "contestant_a",
        "contestant_b",
        "winner",
        "voting_open",
        "voting_ends_at",
        "votes_left",
        "votes_right",
    ]
    list_filter = ["round_number", "voting_open"]
    search_fields = [
        "contestant_a__display_name",
        "contestant_b__display_name",
        "discord_message_id",
    ]
    readonly_fields = [
        "discord_channel_id",
        "discord_message_id",
        "voting_ends_at",
        "votes_left",
        "votes_right",
    ]
    autocomplete_fields = ["contestant_a", "contestant_b", "winner"]
    actions = ["open_next_for_voting", "resolve_due_now"]

    @admin.action(description="Open next match for voting")
    def open_next_for_voting(self, request, queryset):
        # Ignores selection, just advances the queue
        match = open_next_match_for_voting()
        if match is None:
            self.message_user(
                request,
                "Nothing left to open!",
                level=messages.WARNING,
            )
        else:
            self.message_user(
                request,
                f"Now voting on: {match}",
                level=messages.SUCCESS,
            )

    @admin.action(description="Resolve due / selected votes now")
    def resolve_due_now(self, request, queryset):
        from .voting.runner import resolve_due_votes, resolve_vote

        # If they selected open matches, force those; otherwise sweep due ones
        open_selected = queryset.filter(voting_open=True)
        if open_selected.exists():
            n = 0
            for match in open_selected:
                try:
                    if resolve_vote(match, force=True):
                        n += 1
                except Exception as e:
                    self.message_user(
                        request, f"Failed on {match}: {e}", level=messages.ERROR
                    )
            self.message_user(request, f"Resolved {n} selected vote(s).")
        else:
            n = resolve_due_votes()
            self.message_user(request, f"Resolved {n} due vote(s).")


@admin.register(MatchVote)
class MatchVoteAdmin(admin.ModelAdmin):
    list_display = ["match", "user", "choice", "created_at", "updated_at"]
    list_filter = ["choice", "created_at"]
    search_fields = ["user__username", "match__contestant_a__display_name"]
    autocomplete_fields = ["match", "user"]
    readonly_fields = ["created_at", "updated_at"]
