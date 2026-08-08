"""Build Bracketry-shaped JSON from our Match / Contestant rows."""

import math

from django.templatetags.static import static

from .models import Contestant, Match, next_power_of_2

WITHDRAWN_TITLE = "Withdrawn Player"
WITHDRAWN_PFP = "stickers/foxi-sticker-ERROR.png"


def _side_for(contestant, winner_id):
    if contestant is None:
        return {"title": "-"}
    side = {"contestantId": str(contestant.pk)}
    if winner_id is not None:
        side["isWinner"] = contestant.pk == winner_id
    return side


def build_bracketry_data():
    """
    Returns a dict ready for Bracketry's createBracket().
    Empty dict-ish structure if nobody's entered yet.
    """
    contestants = list(Contestant.objects.select_related("user").all())
    matches = list(
        Match.objects.select_related("contestant_a", "contestant_b", "winner").order_by(
            "round_number", "position"
        )
    )

    if not contestants and not matches:
        return {"rounds": [], "matches": [], "contestants": {}}

    size = next_power_of_2(len(contestants)) or 2
    if matches:
        # Prefer whatever tree we already built
        max_round = max(m.round_number for m in matches)
        size = max(size, 2**max_round)

    total_rounds = int(math.log2(size)) if size >= 2 else 1
    withdrawn_pfp = static(WITHDRAWN_PFP)

    contestants_data = {}
    for c in contestants:
        if c.withdrawn:
            contestants_data[str(c.pk)] = {
                "players": [
                    {
                        "title": WITHDRAWN_TITLE,
                        "nationality": withdrawn_pfp,
                    }
                ],
                "profileUrl": "",
                "withdrawn": True,
            }
            continue

        pfp = c.profile_picture.url if c.profile_picture else ""
        contestants_data[str(c.pk)] = {
            "players": [
                {
                    "title": c.display_name,
                    # Bracketry renders this via getNationalityHTML (we use it for pfps)
                    "nationality": pfp,
                }
            ],
            "profileUrl": c.user.get_absolute_url(),
            "withdrawn": False,
        }

    rounds = [{} for _ in range(total_rounds)]
    empty = {"title": "-"}

    bracket_matches = []
    for match in matches:
        sides = []
        winner_id = match.winner_id

        if match.contestant_a:
            sides.append(_side_for(match.contestant_a, winner_id))
        else:
            sides.append(empty)

        if match.contestant_b:
            sides.append(_side_for(match.contestant_b, winner_id))
        else:
            sides.append(empty)

        entry = {
            "roundIndex": match.round_number - 1,
            "order": match.position,
            "sides": sides,
        }
        if match.voting_open:
            entry["isLive"] = True
            entry["matchStatus"] = "Voting!"
        bracket_matches.append(entry)

    return {
        "rounds": rounds,
        "matches": bracket_matches,
        "contestants": contestants_data,
    }
