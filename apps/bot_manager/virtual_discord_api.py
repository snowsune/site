import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

VIRTUAL_GUILD_DEFAULT_ID = "1239663510808563822"
VIRTUAL_GUILD_PATH = (
    Path(settings.BASE_DIR) / "apps" / "bot_manager" / "data" / "virtual_guild.json"
)
DEFAULT_PERMISSIONS = 2147483647


def is_active() -> bool:
    """Virtual mode is enabled whenever DEBUG is True."""
    return bool(getattr(settings, "DEBUG", False))


def is_available() -> bool:
    """Return True when virtual mode is active and data is present."""
    return _get_payload() is not None


def reload():
    """Clear cached payload (mainly for tests)."""
    _load_data.cache_clear()
    _get_payload.cache_clear()


@lru_cache(maxsize=1)
def _load_data() -> Optional[Dict[str, Any]]:
    if not is_active():
        return None

    if not VIRTUAL_GUILD_PATH.exists():
        logger.warning("Virtual guild data file not found at %s", VIRTUAL_GUILD_PATH)
        return None

    try:
        with VIRTUAL_GUILD_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception as exc:  # pragma: no cover - safety
        logger.error("Failed to load virtual guild data: %s", exc)
        return None


def _normalize_member(member: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {**member}
    user_info = normalized.get("user") or {}
    if user_info:
        normalized["user"] = {
            **user_info,
            "id": str(user_info.get("id")) if user_info.get("id") is not None else None,
        }
    normalized["roles"] = [str(role) for role in normalized.get("roles", [])]
    return normalized


def _normalize_channel(channel: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {**channel}
    if "id" in normalized and normalized["id"] is not None:
        normalized["id"] = str(normalized["id"])
    return normalized


@lru_cache(maxsize=1)
def _get_payload() -> Optional[Dict[str, Any]]:
    data = _load_data()
    if not data:
        return None

    # Handle simplified row-style payload (no nested guild sets)
    if "guilds" not in data:
        guild_id = str(data.get("guild_id", VIRTUAL_GUILD_DEFAULT_ID))
        base_guild = {
            "id": guild_id,
            "name": data.get("name", "Virtual Guild"),
            "icon": data.get("icon"),
            "owner": data.get("owner", True),
            "permissions": data.get("permissions", DEFAULT_PERMISSIONS),
        }
        channels: Dict[str, List[Dict[str, Any]]] = {
            guild_id: (
                [
                    _normalize_channel(channel)
                    for channel in data.get("channels", {}).get(guild_id, [])
                ]
                if isinstance(data.get("channels"), dict)
                else [
                    _normalize_channel(channel)
                    for channel in data.get("channels", [])  # type: ignore[arg-type]
                ]
            )
        }
        raw_members = data.get("members") or {}
        members: Dict[str, List[Dict[str, Any]]] = {}
        if isinstance(raw_members, dict):
            members[guild_id] = [
                _normalize_member(member) for member in raw_members.get(guild_id, [])
            ]
        else:
            members[guild_id] = [
                _normalize_member(member) for member in raw_members  # type: ignore[arg-type]
            ]

        users: Dict[str, Dict[str, Any]] = {}
        for member in members.get(guild_id, []):
            user_info = member.get("user")
            if user_info and user_info.get("id"):
                users[str(user_info["id"])] = {
                    **user_info,
                    "id": str(user_info["id"]),
                }

        subscriptions_input = data.get("subscriptions") or []
        if isinstance(subscriptions_input, dict):
            subscriptions = {
                str(gid): list(entries or [])
                for gid, entries in subscriptions_input.items()
            }
        else:
            subscriptions = {guild_id: list(subscriptions_input)}

        user_memberships = data.get("user_memberships") or {}
        if not user_memberships:
            user_memberships = {
                "default": [
                    {"guild_id": guild_id, "permissions": base_guild["permissions"]}
                ],
                "by_discord_id": {},
            }

        fops_settings = {guild_id: data}

        return {
            "guilds": [base_guild],
            "guild_lookup": {guild_id: base_guild},
            "channels": channels,
            "members": members,
            "users": users,
            "user_memberships": {
                "default": (
                    [
                        {
                            "guild_id": str(entry.get("guild_id", guild_id)),
                            "permissions": entry.get(
                                "permissions", DEFAULT_PERMISSIONS
                            ),
                        }
                        for entry in user_memberships.get("default", [])
                    ]
                    if isinstance(user_memberships, dict)
                    else [
                        {
                            "guild_id": guild_id,
                            "permissions": DEFAULT_PERMISSIONS,
                        }
                    ]
                ),
                "by_discord_id": {
                    str(uid): [
                        {
                            "guild_id": str(m.get("guild_id", guild_id)),
                            "permissions": m.get("permissions", DEFAULT_PERMISSIONS),
                        }
                        for m in (memberships or [])
                    ]
                    for uid, memberships in (
                        user_memberships.get("by_discord_id", {}).items()
                        if isinstance(user_memberships, dict)
                        else []
                    )
                },
            },
            "fops_settings": fops_settings,
            "subscriptions": {
                str(guild_id): [dict(sub) for sub in subs]
                for guild_id, subs in subscriptions.items()
            },
        }

    # Full dataset: contains guilds/channels/members/etc.
    guilds: List[Dict[str, Any]] = []
    guild_lookup: Dict[str, Dict[str, Any]] = {}
    for guild in data.get("guilds", []):
        normalized = {**guild}
        normalized["id"] = str(guild.get("id", VIRTUAL_GUILD_DEFAULT_ID))
        guilds.append(normalized)
        guild_lookup[normalized["id"]] = normalized

    channels: Dict[str, List[Dict[str, Any]]] = {}
    for gid, channel_list in (data.get("channels") or {}).items():
        gid_str = str(gid)
        channels[gid_str] = [
            _normalize_channel(channel) for channel in channel_list or []
        ]

    members: Dict[str, List[Dict[str, Any]]] = {}
    for gid, member_list in (data.get("members") or {}).items():
        gid_str = str(gid)
        members[gid_str] = [_normalize_member(member) for member in member_list or []]

    users: Dict[str, Dict[str, Any]] = {}
    for user_id, info in (data.get("users") or {}).items():
        uid_str = str(user_id)
        users[uid_str] = {**info, "id": uid_str}

    subscriptions = {
        str(gid): [dict(sub) for sub in subs or []]
        for gid, subs in (data.get("subscriptions") or {}).items()
    }

    return {
        "guilds": guilds,
        "guild_lookup": guild_lookup,
        "channels": channels,
        "members": members,
        "users": users,
        "user_memberships": data.get("user_memberships") or {},
        "fops_settings": data.get("fops_settings") or {},
        "subscriptions": subscriptions,
    }


def get_bot_guilds() -> List[Dict[str, Any]]:
    payload = _get_payload()
    return payload["guilds"] if payload else []


def get_user_guilds(user) -> List[Dict[str, Any]]:
    payload = _get_payload()
    if not payload:
        return []

    discord_id = str(getattr(user, "discord_id", "") or "") or None
    memberships_config = payload.get("user_memberships") or {}
    by_id = {
        str(uid): entries
        for uid, entries in (memberships_config.get("by_discord_id") or {}).items()
    }

    memberships = []
    if discord_id and discord_id in by_id:
        memberships = by_id[discord_id] or []
    else:
        memberships = memberships_config.get("default", []) or []

    guilds: List[Dict[str, Any]] = []
    for membership in memberships:
        guild_id = str(membership.get("guild_id", VIRTUAL_GUILD_DEFAULT_ID))
        guild = payload["guild_lookup"].get(guild_id)
        if not guild:
            continue
        merged = {**guild}
        merged["permissions"] = membership.get(
            "permissions", guild.get("permissions", DEFAULT_PERMISSIONS)
        )
        guilds.append(merged)

    return guilds


def get_guild_channels(guild_id: Any) -> List[Dict[str, Any]]:
    payload = _get_payload()
    if not payload:
        return []
    return payload["channels"].get(str(guild_id), [])


def get_user_info(user_id: Any) -> Optional[Dict[str, Any]]:
    payload = _get_payload()
    if not payload:
        return None
    return payload["users"].get(str(user_id))


def get_guild_members(guild_id: Any, max_members: int = 5000) -> List[Dict[str, Any]]:
    payload = _get_payload()
    if not payload:
        return []
    return payload["members"].get(str(guild_id), [])[:max_members]


def get_fops_guild(guild_id: Any) -> Optional[Dict[str, Any]]:
    payload = _get_payload()
    if not payload:
        return None
    return payload["fops_settings"].get(str(guild_id))


def get_fops_subscriptions(guild_id: Any) -> List[Dict[str, Any]]:
    payload = _get_payload()
    if not payload:
        return []
    return payload["subscriptions"].get(str(guild_id), [])


def get_all_fops_subscriptions() -> List[Dict[str, Any]]:
    payload = _get_payload()
    if not payload:
        return []
    all_subs: List[Dict[str, Any]] = []
    for subs in payload["subscriptions"].values():
        all_subs.extend(list(subs))
    return all_subs
