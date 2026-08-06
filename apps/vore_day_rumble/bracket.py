"""Build Bracketry-shaped JSON from our Match / Contestant rows."""

import math

from .models import Contestant, Match, next_power_of_2


def _round_name(round_number, bracket_size):
    remaining = bracket_size // (2 ** (round_number - 1))
    if remaining == 2:
        return "Final"
    if remaining == 4:
        return "Semifinals"
    if remaining == 8:
        return "Quarterfinals"
    return f"Round of {remaining}"


def _side_for(contestant, winner_id):
    if contestant is None:
        return {"title": "TBD"}
    side = {"contestantId": str(contestant.pk)}
    if winner_id is not None:
        side["isWinner"] = contestant.pk == winner_id
    return side


def build_bracketry_data():
    """
    Returns a dict ready for Bracketry's createBracket().
    Empty dict-ish structure if nobody's entered yet.
    """
    contestants = list(Contestant.objects.all())
    matches = list(
        Match.objects.select_related(
            "contestant_a", "contestant_b", "winner"
        ).order_by("round_number", "position")
    )

    if not contestants and not matches:
        return {"rounds": [], "matches": [], "contestants": {}}

    size = next_power_of_2(len(contestants)) or 2
    if matches:
        # Prefer whatever tree we already built
        max_round = max(m.round_number for m in matches)
        size = max(size, 2**max_round)

    total_rounds = int(math.log2(size)) if size >= 2 else 1

    contestants_data = {}
    for c in contestants:
        pfp = c.profile_picture.url if c.profile_picture else ""
        contestants_data[str(c.pk)] = {
            "players": [
                {
                    "title": c.display_name,
                    # Bracketry renders this via getNationalityHTML (we use it for pfps)
                    "nationality": pfp,
                }
            ],
        }

    rounds = [
        {"name": _round_name(r, size)} for r in range(1, total_rounds + 1)
    ]

    bracket_matches = []
    for match in matches:
        sides = []
        winner_id = match.winner_id

        if match.contestant_a:
            sides.append(_side_for(match.contestant_a, winner_id))
        elif match.contestant_b and winner_id == match.contestant_b_id:
            # Pure bye on the A side
            sides.append({"title": "BYE"})
        else:
            sides.append({"title": "TBD"} if match.round_number > 1 else {"title": "BYE"})

        if match.contestant_b:
            sides.append(_side_for(match.contestant_b, winner_id))
        elif match.contestant_a and winner_id == match.contestant_a_id:
            sides.append({"title": "BYE"})
        else:
            sides.append({"title": "TBD"} if match.round_number > 1 else {"title": "BYE"})

        entry = {
            "roundIndex": match.round_number - 1,
            "order": match.position,
            "sides": sides,
        }
        if match.voting_open:
            entry["isLive"] = True
            entry["matchStatus"] = "Voting!"
        elif match.winner_id and (
            not match.contestant_a or not match.contestant_b
        ):
            entry["matchStatus"] = "Bye"
        bracket_matches.append(entry)

    return {
        "rounds": rounds,
        "matches": bracket_matches,
        "contestants": contestants_data,
    }
