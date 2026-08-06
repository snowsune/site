"""
BIG runner!
Has all the steps in order (ish~)

start_vote(match)   - composite, post to Discord (with link + countdown), set timer
resolve_vote(match) - tally site votes, pick a winner, post results to Discord
resolve_due_votes() - sweep anything whose timer already elapsed
"""

import logging
import random
import threading
from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections
from django.db.models import Max
from django.utils import timezone

from ..models import Match, RumbleSettings, advance_winners_into_next_rounds
from . import discord as discord_api
from .composite import create_matchup_image, create_winner_image

logger = logging.getLogger(__name__)


def start_vote(match):
    """
    Kick off a match vote: announce on Discord, open site voting, set timer.
    """
    if not match.contestant_a or not match.contestant_b:
        logger.warning("Match %s isn't a real matchup, skipping vote", match.pk)
        return False

    rumble = RumbleSettings.get()
    channel_id = (rumble.discord_channel_id or "").strip()
    if not channel_id:
        logger.error("No discord_channel_id set on Rumble Settings")
        return False

    a = match.contestant_a
    b = match.contestant_b
    minutes = rumble.vote_duration_minutes or 30
    ends_at = timezone.now() + timedelta(minutes=minutes)
    ends_unix = int(ends_at.timestamp())
    vote_url = f"{settings.SITE_URL.rstrip('/')}/voreday/"

    image = create_matchup_image(a, b)
    content = (
        f"**Vixi's Vore Day Rumble!**\n"
        f"**{a.display_name}** vs **{b.display_name}**\n"
        f"Vote on snowsune.net: {vote_url}\n"
        f"Closes <t:{ends_unix}:R>."
    )

    message_id = discord_api.post_matchup(channel_id, content, image)

    # Fresh site tallies for this match window
    match.votes.all().delete()

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
    Tally site votes and crown a winner. Posts results to Discord.
    Returns the winning Contestant, or None if nothing to do.
    """
    if match.winner_id and not force:
        return match.winner

    if (
        not force
        and match.voting_ends_at
        and match.voting_ends_at > timezone.now()
    ):
        logger.info(
            "Match %s vote still running until %s", match.pk, match.voting_ends_at
        )
        return None

    if not match.contestant_a or not match.contestant_b:
        logger.warning("Match %s missing contestants, closing vote", match.pk)
        match.voting_open = False
        match.save(update_fields=["voting_open"])
        return None

    left, right = match.live_vote_counts()

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
        f"**Results!** **{a_name}**: **{left}** | **{b_name}**: **{right}**\n"
    )
    if tie:
        result += f"Omg a tie! Coin flip goes to **{winner.display_name}**!~"
    else:
        result += f"**{winner.display_name}** advances!~"

    channel_id = (match.discord_channel_id or "").strip()
    if not channel_id:
        channel_id = (RumbleSettings.get().discord_channel_id or "").strip()

    if channel_id:
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

    announce_champion_if_crowned(channel_id=channel_id or None)
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

    rumble = RumbleSettings.get()
    if rumble.champion_announced:
        return champion

    channel_id = (channel_id or rumble.discord_channel_id or "").strip()
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
        rumble.champion_announced = True
        rumble.save(update_fields=["champion_announced"])
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
