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

    class Meta:
        verbose_name = "Rumble Settings"
        verbose_name_plural = "Rumble Settings"

    def __str__(self):
        return "Vore Day Rumble Settings"

    def save(self, *args, **kwargs):
        should_advance = self.advance_to_next_match
        self.advance_to_next_match = False
        self.pk = 1
        super().save(*args, **kwargs)
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
    """One matchup in a round. Full tree gets rebuilt whenever someone signs up."""

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

    class Meta:
        ordering = ["round_number", "position"]
        unique_together = [["round_number", "position"]]
        verbose_name_plural = "Matches"

    def __str__(self):
        a = self.contestant_a.display_name if self.contestant_a else "TBD"
        b = self.contestant_b.display_name if self.contestant_b else "BYE"
        status = " [voting]" if self.voting_open else ""
        return f"R{self.round_number} M{self.position}: {a} vs {b}{status}"


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


@transaction.atomic
def open_next_match_for_voting():
    """Close the current match, open the next unfinished one. Returns it (or None)."""
    Match.objects.filter(voting_open=True).update(voting_open=False)

    nxt = (
        Match.objects.filter(winner__isnull=True)
        .filter(contestant_a__isnull=False, contestant_b__isnull=False)
        .order_by("round_number", "position")
        .first()
    )
    if nxt is None:
        # Maybe a half-filled match with a bye slipped through
        bye = (
            Match.objects.filter(winner__isnull=True, contestant_a__isnull=False)
            .filter(contestant_b__isnull=True)
            .order_by("round_number", "position")
            .first()
        )
        if bye is None:
            bye = (
                Match.objects.filter(winner__isnull=True, contestant_b__isnull=False)
                .filter(contestant_a__isnull=True)
                .order_by("round_number", "position")
                .first()
            )
        if bye is None:
            return None
        bye.winner = bye.contestant_a or bye.contestant_b
        bye.voting_open = False
        bye.save(update_fields=["winner", "voting_open"])
        advance_winners_into_next_rounds()
        return open_next_match_for_voting()

    nxt.voting_open = True
    nxt.save(update_fields=["voting_open"])
    return nxt
