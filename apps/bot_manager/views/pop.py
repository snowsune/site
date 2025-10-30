from django.shortcuts import render
from django.conf import settings
import os
import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from .. import discord_api


def pop_view(request):
    guild_id = "1153521286086148156"  # Just for bixi

    # Load species mapping from YAML
    species_map_path = os.path.join(
        settings.BASE_DIR, "apps", "bot_manager", "data", "species_roles_map.yaml"
    )
    species_map = {}
    yaml_loaded = False
    if yaml is not None and os.path.exists(species_map_path):
        try:
            with open(species_map_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                species_map = {
                    str(species): {str(rid) for rid in (ids or [])}
                    for species, ids in loaded.items()
                }
                yaml_loaded = True
        except Exception:
            species_map = {}

    # Counting mode: default to 'first'; use 'hybrid' when explicitly requested
    mode = "hybrid" if request.GET.get("hybrid") else "first"

    # Build role_id -> species list mapping and species order
    role_to_species = {}
    species_order = list(species_map.keys())
    for species, role_ids in species_map.items():
        for rid in role_ids:
            role_to_species.setdefault(rid, []).append(species)

    # Fetch guild members (cached)
    members = discord_api.get_guild_members(guild_id)
    members_count = len(members) if isinstance(members, list) else 0

    # Initialize counts
    species_counts = {species: 0 for species in species_order}

    matched_members = 0
    for member in members:
        member_role_ids = [str(r) for r in member.get("roles", [])]
        matched_species = set()
        for rid in member_role_ids:
            for sp in role_to_species.get(rid, []):
                matched_species.add(sp)

        if not matched_species:
            continue

        matched_members += 1
        if mode == "first":
            first = next((sp for sp in species_order if sp in matched_species), None)
            if first is not None:
                species_counts[first] += 1
        else:
            for sp in matched_species:
                species_counts[sp] += 1

    # Prepare chart data (filter zeros) and sort by count desc
    items = [
        (sp, species_counts.get(sp, 0))
        for sp in species_order
        if species_counts.get(sp, 0) > 0
    ]
    items.sort(key=lambda x: x[1], reverse=True)
    chart_labels = [sp for sp, _ in items]
    chart_values = [cnt for _, cnt in items]

    error_messages = []
    if not yaml_loaded:
        error_messages.append(
            "YAML mapping not loaded; ensure PyYAML is installed and the file exists."
        )
    if members_count == 0:
        error_messages.append(
            "No members fetched. The bot likely needs the Guild Members intent enabled."
        )

    context = {
        "guild_id": guild_id,
        "mode": mode,
        "chart_labels": json.dumps(chart_labels),
        "chart_values": json.dumps(chart_values),
        "members_count": members_count,
        "matched_members": matched_members,
        "errors": error_messages,
    }
    response = render(request, "bot_manager/pop.html", context)
    response["Vary"] = "Cookie"
    return response
