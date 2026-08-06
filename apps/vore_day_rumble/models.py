import math
import random

from django.conf import settings
from django.db import models, transaction
from django.db.models import Max


class RumbleSettings(models.Model):
    """
    All the rumble settings.
    Admins flip these in django admin~
    """

    enabled = models.BooleanField(
        default=False,
        help_text="Master switch. Off = come back next year!",
    )
    signups_open = models.BooleanField(
        default=False,
        help_text="Allow new contestants to sign up",
    )
    advance_to_next_match = models.BooleanField(
        default=False,
        help_text="Check + save to open the next match for voting. Clears itself after.",
    )
    reset_bracket = models.BooleanField(
        default=False,
        help_text="Check + save to wipe winners/votes and reshuffle everyone. Clears itself after.",
    )
    discord_channel_id = models.CharField(
        max_length=40,
        blank=True,
        help_text="Discord channel ID for matchup announcements + results",
    )
    vote_duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="How long each site vote stays open",
    )
    champion_announced = models.BooleanField(
        default=False,
        help_text="Internal: already posted the WINNER card for this bracket.",
    )

    class Meta:
        verbose_name = "Rumble Settings"
        verbose_name_plural = "Rumble Settings"

    def __str__(self):
        return "Vore Day Rumble Settings"

    def save(self, *args, **kwargs):
        should_advance = self.advance_to_next_match
        should_reset = self.reset_bracket
        self.advance_to_next_match = False
        self.reset_bracket = False
        self.pk = 1
        super().save(*args, **kwargs)
        if should_reset:
            reshuffle_bracket()
        if should_advance:
            open_next_match_for_voting()

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Contestant(models.Model):
    """A signed-up participant <3"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vore_day_rumble_entry",
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Name shown on the bracket (username or character name <3)",
    )
    profile_picture = models.ImageField(
        upload_to="vore_day_rumble/pfps/",
        blank=True,
        null=True,
    )
    bracket_position = models.PositiveIntegerField(
        default=0,
        help_text="Slot in the bracket",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["bracket_position", "created_at"]

    def __str__(self):
        return self.display_name


class Match(models.Model):
    """One matchup in a round. Round 1 gets rebuilt whenever someone signs up."""

    round_number = models.PositiveIntegerField(default=1)
    position = models.PositiveIntegerField(
        help_text="Order in the round (0-based)",
    )
    contestant_a = models.ForeignKey(
        Contestant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches_as_a",
    )
    contestant_b = models.ForeignKey(
        Contestant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches_as_b",
    )
    winner = models.ForeignKey(
        Contestant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches_won",
    )
    voting_open = models.BooleanField(
        default=False,
        help_text="Is this the match folks are voting on right now?",
    )
    discord_channel_id = models.CharField(max_length=40, blank=True)
    discord_message_id = models.CharField(max_length=40, blank=True)
    voting_ends_at = models.DateTimeField(null=True, blank=True)
    votes_left = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Final tally for contestant A (set when vote closes)",
    )
    votes_right = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Final tally for contestant B (set when vote closes)",
    )

    class Meta:
        ordering = ["round_number", "position"]
        unique_together = [["round_number", "position"]]
        verbose_name_plural = "Matches"

    def __str__(self):
        a = self.contestant_a.display_name if self.contestant_a else "TBD"
        b = self.contestant_b.display_name if self.contestant_b else "BYE"
        status = " [voting]" if self.voting_open else ""
        return f"R{self.round_number} M{self.position}: {a} vs {b}{status}"

    def live_vote_counts(self):
        """Current site tallies (A / B)."""
        from django.db.models import Count, Q

        agg = self.votes.aggregate(
            left=Count("id", filter=Q(choice=MatchVote.CHOICE_A)),
            right=Count("id", filter=Q(choice=MatchVote.CHOICE_B)),
        )
        return agg["left"] or 0, agg["right"] or 0


class MatchVote(models.Model):
    """One anonymous site vote per snowsune account, per match."""

    CHOICE_A = "a"
    CHOICE_B = "b"
    CHOICE_CHOICES = [
        (CHOICE_A, "Contestant A"),
        (CHOICE_B, "Contestant B"),
    ]

    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vore_day_rumble_votes",
    )
    choice = models.CharField(max_length=1, choices=CHOICE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["match", "user"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} -> {self.choice} on match {self.match_id}"


def next_power_of_2(n):
    """Bracket size. 1 entrant still gets a 2-slot bracket (them vs bye)."""
    if n <= 0:
        return 0
    if n == 1:
        return 2
    p = 1
    while p < n:
        p *= 2
    return p


def advance_winners_into_next_rounds():
    """Push known winners into the next round's slots."""
    max_round = Match.objects.aggregate(m=Max("round_number"))["m"] or 1
    for r in range(1, max_round):
        for match in Match.objects.filter(
            round_number=r, winner__isnull=False
        ).order_by("position"):
            nxt = Match.objects.filter(
                round_number=r + 1, position=match.position // 2
            ).first()
            if not nxt:
                continue
            if match.position % 2 == 0:
                nxt.contestant_a = match.winner
            else:
                nxt.contestant_b = match.winner
            nxt.save(update_fields=["contestant_a", "contestant_b"])


@transaction.atomic
def reshuffle_bracket():
    """
    Shuffle everyone and rebuild a full single-elim tree
    (padded to the next power of 2, with bye auto-wins).
    """
    contestants = list(Contestant.objects.all())
    random.shuffle(contestants)

    for i, contestant in enumerate(contestants):
        contestant.bracket_position = i
    if contestants:
        Contestant.objects.bulk_update(contestants, ["bracket_position"])

    # Signups still open = wipe the whole tree and rebuild
    Match.objects.all().delete()
    settings = RumbleSettings.get()
    if settings.champion_announced:
        settings.champion_announced = False
        settings.save(update_fields=["champion_announced"])

    size = next_power_of_2(len(contestants))
    if size == 0:
        return

    total_rounds = int(math.log2(size))
    byes_needed = size - len(contestants)

    # First N players get byes; the rest play round 1. No empty-vs-empty slots.
    pairs = []
    for p in contestants[:byes_needed]:
        pairs.append((p, None))
    rest = contestants[byes_needed:]
    for i in range(0, len(rest), 2):
        pairs.append((rest[i], rest[i + 1]))
    random.shuffle(pairs)

    for i, (a, b) in enumerate(pairs):
        winner = a if a and not b else (b if b and not a else None)
        Match.objects.create(
            round_number=1,
            position=i,
            contestant_a=a,
            contestant_b=b,
            winner=winner,
        )

    # Empty later rounds (filled as winners land)
    for r in range(2, total_rounds + 1):
        for i in range(size // (2**r)):
            Match.objects.create(round_number=r, position=i)

    advance_winners_into_next_rounds()


def open_next_match_for_voting():
    """
    Resolve any open vote, then open the next unfinished matchup and
    announce it (site voting + Discord). Returns the newly opened Match, or None.
    """
    current = Match.objects.filter(voting_open=True).first()
    if current:
        from .voting.runner import resolve_vote

        try:
            resolve_vote(current, force=True)
        except Exception:
            Match.objects.filter(pk=current.pk).update(voting_open=False)

    match = _claim_next_matchup()
    if match is None:
        # Nothing left to vote on - if the finals are done, show the WINNER card
        from .voting.runner import announce_champion_if_crowned

        announce_champion_if_crowned()
        return None
    return _start_discord_for(match)


def _claim_next_matchup():
    """
    Find the next votable match (auto-resolving byes along the way)
    and mark it voting_open. Discord happens after this returns.
    """
    while True:
        with transaction.atomic():
            nxt = (
                Match.objects.filter(winner__isnull=True)
                .filter(contestant_a__isnull=False, contestant_b__isnull=False)
                .order_by("round_number", "position")
                .first()
            )
            if nxt is not None:
                nxt.voting_open = True
                nxt.save(update_fields=["voting_open"])
                return nxt

            bye = (
                Match.objects.filter(
                    winner__isnull=True,
                    round_number=1,  # Only round-1 padding byes, not "waiting on feeder"
                )
                .exclude(contestant_a__isnull=True, contestant_b__isnull=True)
                .filter(
                    models.Q(contestant_a__isnull=True)
                    | models.Q(contestant_b__isnull=True)
                )
                .order_by("round_number", "position")
                .first()
            )
            if bye is None:
                return None

            bye.winner = bye.contestant_a or bye.contestant_b
            bye.voting_open = False
            bye.save(update_fields=["winner", "voting_open"])
            advance_winners_into_next_rounds()


def _start_discord_for(match):
    from .voting.runner import start_vote

    try:
        start_vote(match)
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Failed to start Discord vote for match %s", match.pk
        )
    return match
