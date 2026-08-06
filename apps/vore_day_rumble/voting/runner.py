"""
BIG runner!
Has all the steps in order (ish~)


start_vote(match)   - composite, post to Discord, seed reacts, set timer
resolve_vote(match) - tally reacts, pick a winner, advance bracket
resolve_due_votes() - sweep anything whose timer already elapsed
  (also called from /voreday/ and as a fallback if the worker restarted)
"""

import logging
import random
import threading
import time
from datetime import timedelta

from django.db import close_old_connections
from django.utils import timezone

from django.db.models import Max

from ..models import Match, RumbleSettings, advance_winners_into_next_rounds
from . import discord as discord_api
from .composite import create_matchup_image, create_winner_image

logger = logging.getLogger(__name__)


def start_vote(match):
    """
    Kick off Discord voting for an open match.
    Safe to call only when both sides are filled <3
    """

    if not match.contestant_a or not match.contestant_b:
        logger.warning("Match %s isn't a real matchup, skipping vote", match.pk) # like if blank from the js lib
        return False

    settings = RumbleSettings.get()
    channel_id = (settings.discord_channel_id or "").strip()
    if not channel_id:
        logger.error("No discord_channel_id set on Rumble Settings")
        return False

    a = match.contestant_a
    b = match.contestant_b
    minutes = settings.vote_duration_minutes or 30

    image = create_matchup_image(a, b)
    ends_at = timezone.now() + timedelta(minutes=minutes)
    ends_unix = int(ends_at.timestamp())
    content = (
        f"**Vixi's Vore Day Rumble!**\n"
        f"{discord_api.LEFT_EMOJI} **{a.display_name}** vs "
        f"**{b.display_name}** {discord_api.RIGHT_EMOJI}\n"
        f"React to vote! Closes <t:{ends_unix}:R>."
    )

    message_id = discord_api.post_matchup(channel_id, content, image)

    # Persist the Discord message ASAP so a flaky react doesn't leave us stranded
    match.discord_channel_id = channel_id
    match.discord_message_id = message_id
    match.voting_ends_at = ends_at
    match.votes_left = None
    match.votes_right = None
    match.voting_open = True
    match.save(
        update_fields=[
            "discord_channel_id",
            "discord_message_id",
            "voting_ends_at",
            "votes_left",
            "votes_right",
            "voting_open",
        ]
    )

    # Seed reacts one at a time with a tiny gap (Discord rate-limits :<)
    for emoji in (discord_api.LEFT_EMOJI, discord_api.RIGHT_EMOJI):
        try:
            discord_api.add_reaction(channel_id, message_id, emoji)
        except Exception:
            logger.exception(
                "Couldn't seed %s react on match %s (msg %s) - vote is still live",
                emoji,
                match.pk,
                message_id,
            )
        time.sleep(0.4)

    _schedule_resolve(match.pk, match.voting_ends_at)
    logger.info(
        "Started vote for match %s (msg %s, ends %s)",
        match.pk,
        message_id,
        match.voting_ends_at,
    )
    return True


def _schedule_resolve(match_id, ends_at):
    """Fire resolve_vote in a daemon thread when the timer hits."""
    delay = max(1.0, (ends_at - timezone.now()).total_seconds()) + 2.0

    def _run():
        close_old_connections()
        try:
            match = Match.objects.filter(pk=match_id, voting_open=True).first()
            if match is None:
                return
            resolve_vote(match)
        except Exception:
            logger.exception("Background resolve failed for match %s", match_id)
        finally:
            close_old_connections()

    timer = threading.Timer(delay, _run)
    timer.daemon = True
    timer.start()
    logger.info("Scheduled resolve for match %s in %.0fs", match_id, delay)


def resolve_vote(match, force=False):
    """
    Tally reactions and crown a winner.
    Returns the winning Contestant, or None if nothing to do.
    """
    if match.winner_id and not force:
        return match.winner

    if not match.discord_message_id or not match.discord_channel_id:
        logger.warning(
            "Match %s has no Discord message to tally - closing vote without a winner",
            match.pk,
        )
        match.voting_open = False
        match.save(update_fields=["voting_open"])
        return None

    if (
        not force
        and match.voting_ends_at
        and match.voting_ends_at > timezone.now()
    ):
        logger.info(
            "Match %s vote still running until %s", match.pk, match.voting_ends_at
        )
        return None

    channel_id = match.discord_channel_id
    message_id = match.discord_message_id

    left = discord_api.count_reactions(
        channel_id, message_id, discord_api.LEFT_EMOJI
    )
    right = discord_api.count_reactions(
        channel_id, message_id, discord_api.RIGHT_EMOJI
    )

    tie = False
    if left > right:
        winner = match.contestant_a
    elif right > left:
        winner = match.contestant_b
    else:
        tie = True
        winner = random.choice([match.contestant_a, match.contestant_b])

    match.votes_left = left
    match.votes_right = right
    match.winner = winner
    match.voting_open = False
    match.save(
        update_fields=[
            "votes_left",
            "votes_right",
            "winner",
            "voting_open",
        ]
    )
    advance_winners_into_next_rounds()

    a_name = match.contestant_a.display_name
    b_name = match.contestant_b.display_name
    result = (
        f"**Results!** {discord_api.LEFT_EMOJI} {a_name}: **{left}** | "
        f"{b_name}: **{right}** {discord_api.RIGHT_EMOJI}\n"
    )
    if tie:
        result += f"Omg a tie! Coin flip goes to **{winner.display_name}**!~"
    else:
        result += f"**{winner.display_name}** advances!~"

    try:
        discord_api.post_text(channel_id, result)
    except Exception as e:
        logger.error("Couldn't post results message: %s", e)

    logger.info(
        "Resolved match %s: %s wins (%s-%s)%s",
        match.pk,
        winner.display_name,
        left,
        right,
        " [tie]" if tie else "",
    )

    # Finals done???? Post the big WINNER card!
    announce_champion_if_crowned(channel_id=channel_id)

    return winner


def get_tournament_champion():
    """Winner of the final match, but only once the bracket is fully settled."""
    max_round = Match.objects.aggregate(m=Max("round_number"))["m"]
    if not max_round:
        return None

    remaining = Match.objects.filter(
        winner__isnull=True,
        contestant_a__isnull=False,
        contestant_b__isnull=False,
    )
    if remaining.exists():
        return None

    final = Match.objects.filter(round_number=max_round, position=0).first()
    if final and final.winner_id:
        return final.winner
    return None


def announce_champion_if_crowned(channel_id=None):
    """
    If the rumble has a final winner, post the WINNER image once.
    Returns the champion Contestant, or None.
    """
    champion = get_tournament_champion()
    if champion is None:
        return None

    settings = RumbleSettings.get()
    if settings.champion_announced:
        return champion

    channel_id = (channel_id or settings.discord_channel_id or "").strip()
    if not channel_id:
        logger.error("No discord channel for winner announcement")
        return champion

    try:
        image = create_winner_image(champion)
        content = (
            f"**The Vore Day Rumble is over!**\n"
            f"**{champion.display_name}** wins!~ (Uurp~)"
        )
        discord_api.post_matchup(
            channel_id, content, image, filename="winner.png"
        )
        settings.champion_announced = True
        settings.save(update_fields=["champion_announced"])
        logger.info("Posted WINNER card for %s", champion.display_name)
    except Exception:
        logger.exception("Failed to post WINNER card for %s", champion.display_name)

    return champion


def resolve_due_votes():
    """Resolve every open vote whose timer has elapsed. Returns count resolved."""
    now = timezone.now()
    due = Match.objects.filter(
        voting_open=True,
        voting_ends_at__isnull=False,
        voting_ends_at__lte=now,
        winner__isnull=True,
    )
    resolved = 0
    for match in due:
        try:
            if resolve_vote(match):
                resolved += 1
        except Exception as e:
            logger.exception("Failed resolving match %s: %s", match.pk, e)
    return resolved
