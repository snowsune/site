"""
Live vote status for SSE
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Iterator

from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_cv = threading.Condition(_lock)
_version = 0
_snapshot: dict[str, Any] = {"voting_open": False}
_subscribers = 0
_poller: threading.Thread | None = None

POLL_SECONDS = 1.0


def active_match():
    from ..models import Match

    return (
        Match.objects.filter(voting_open=True)
        .select_related("contestant_a", "contestant_b")
        .first()
    )


def _shared_snapshot(match=None) -> dict[str, Any]:
    """Tallies + countdown (no per-user fields)."""
    if match is None:
        match = active_match()
    if match is None or not match.contestant_a or not match.contestant_b:
        return {"voting_open": False}

    left, right = match.live_vote_counts()
    ends_at = match.voting_ends_at
    return {
        "match_id": match.pk,
        "voting_open": True,
        "votes_left": left,
        "votes_right": right,
        "ends_at_unix": int(ends_at.timestamp()) if ends_at else None,
        "server_now_unix": int(timezone.now().timestamp()),
    }


def snapshot_for(user=None, match=None, base=None) -> dict[str, Any]:
    """Status payload for the UI: shared tallies + my_choice."""
    snap = dict(base) if base is not None else _shared_snapshot(match)
    snap["my_choice"] = None
    snap["server_now_unix"] = int(timezone.now().timestamp())
    if (
        not snap.get("voting_open")
        or user is None
        or not getattr(user, "is_authenticated", False)
    ):
        return snap

    from ..models import MatchVote

    match_id = snap.get("match_id")
    if not match_id:
        return snap
    vote = MatchVote.objects.filter(match_id=match_id, user=user).first()
    if vote:
        snap["my_choice"] = vote.choice
    return snap


def _snap_key(snap: dict[str, Any]) -> tuple:
    return (
        snap.get("match_id"),
        snap.get("voting_open"),
        snap.get("votes_left"),
        snap.get("votes_right"),
        snap.get("ends_at_unix"),
    )


def _poller_loop() -> None:
    global _poller, _version, _snapshot
    last_key = None
    try:
        while True:
            close_old_connections()
            try:
                snap = _shared_snapshot()
            except Exception:
                logger.exception("Vote live poller failed")
                snap = {"voting_open": False}

            key = _snap_key(snap)
            with _cv:
                if key != last_key:
                    last_key = key
                    _snapshot = snap
                    _version += 1
                    _cv.notify_all()
                elif _subscribers <= 0:
                    _poller = None
                    return
                _cv.wait(timeout=POLL_SECONDS)
    finally:
        close_old_connections()
        with _lock:
            if _poller is threading.current_thread():
                _poller = None


def subscribe() -> int:
    global _subscribers, _poller
    with _cv:
        _subscribers += 1
        if _poller is None or not _poller.is_alive():
            _poller = threading.Thread(
                target=_poller_loop,
                name="vore-day-rumble-vote-live",
                daemon=True,
            )
            _poller.start()
        _cv.notify_all()
        return _version


def unsubscribe() -> None:
    global _subscribers
    with _cv:
        _subscribers = max(0, _subscribers - 1)
        _cv.notify_all()


def notify() -> None:
    """Wake the poller after a vote cast / match open / resolve."""
    with _cv:
        _cv.notify_all()


def wait_for_update(
    last_version: int, timeout: float = 15.0
) -> tuple[int, dict[str, Any]]:
    with _cv:
        if _version == last_version:
            _cv.wait(timeout=timeout)
        return _version, dict(_snapshot)


def iter_sse(user) -> Iterator[str]:
    """SSE frames for one watcher (status events + keepalives)."""
    version = subscribe()
    try:
        version, snap = wait_for_update(version, timeout=2.0)
        while True:
            payload = snapshot_for(user, base=snap)
            yield (
                f"id: {version}\n"
                f"event: status\n"
                f"data: {json.dumps(payload)}\n\n"
            )
            if not snap.get("voting_open"):
                return

            while True:
                prev = version
                version, snap = wait_for_update(prev, timeout=15.0)
                if version != prev:
                    break
                yield ": keepalive\n\n"
    except GeneratorExit:
        return
    finally:
        unsubscribe()
