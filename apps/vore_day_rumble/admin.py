from django.contrib import admin, messages

from .models import Contestant, Match, RumbleSettings, open_next_match_for_voting


@admin.register(RumbleSettings)
class RumbleSettingsAdmin(admin.ModelAdmin):
    list_display = ["__str__", "enabled", "signups_open"]
    fieldsets = (
        (
            "Toggles",
            {
                "fields": ("enabled", "signups_open", "advance_to_next_match"),
                "description": (
                    "enabled = site is live, signups_open = /voreday/enter works, "
                    "advance_to_next_match = check + save to kick off the next vote."
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
        "has_pfp",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["display_name", "user__username"]
    readonly_fields = ["bracket_position", "created_at", "updated_at"]
    autocomplete_fields = ["user"]
    ordering = ["bracket_position"]

    @admin.display(boolean=True, description="Has PFP")
    def has_pfp(self, obj):
        return bool(obj.profile_picture)


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
    ]
    list_filter = ["round_number", "voting_open"]
    search_fields = [
        "contestant_a__display_name",
        "contestant_b__display_name",
    ]
    autocomplete_fields = ["contestant_a", "contestant_b", "winner"]
    actions = ["open_next_for_voting"]

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
