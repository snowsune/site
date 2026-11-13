"""
PROTOTYPEE

TODO: Use actual models and stuff!

This is all completely harcoded and temporary! REPLACE ME LATER
"""

# Default art (relative to static/)
PLACEHOLDER_ART = "lists/placeholder.png"


def _sample_episodes(show_title):
    """Random sample episodes!"""
    return [
        {
            "number": 3,
            "title": "Placeholder Episode Three",
            "date": "2026-11-01",
            "description": f"The newest episode of {show_title} here!",
            "tags": ["foxes", "frrts"],
        },
        {
            "number": 2,
            "title": "Placeholder Episode Two",
            "date": "2026-10-15",
            "description": "Summarry...",
            "tags": ["canines"],
        },
        {
            "number": 1,
            "title": "Pilot",
            "date": "2026-10-01",
            "description": "Pilot thing first sumary here!",
            "tags": ["vore"],
        },
    ]


def _show(slug, title, hosts, tagline):
    return {
        "slug": slug,
        "title": title,
        "hosts": hosts,
        "tagline": tagline,
        "art": PLACEHOLDER_ART,
        "bio": (f"{title} is a placeholder! FILL ME OUT LATER."),
        "links": [
            {"label": "Website", "url": "#"},
            {"label": "RSS", "url": "#"},
            {"label": "Spotify", "url": "#"},
        ],
        "episodes": _sample_episodes(title),
    }


LISTS = {
    "furcasts": {
        "slug": "furcasts",
        "title": "Furcasts",
        "description": "A directory of furry podcasts!",
        "items": [
            _show(
                "placeholder-one",
                "Placeholder Podcast One",
                ["Host A", "Host B"],
                "Weekly fluff and news",
            ),
            _show(
                "placeholder-two",
                "Placeholder Podcast Two",
                ["Host C"],
                "Interviews with furs",
            ),
            _show(
                "placeholder-three",
                "Placeholder Podcast Three",
                ["Host D", "Host E"],
                "Con stories and things",
            ),
            _show(
                "placeholder-four", "Placeholder Podcast Four", ["Host F"], "Art talk"
            ),
            _show(
                "placeholder-five",
                "Placeholder Podcast Five",
                ["Host G", "Host H"],
                "Suits and tips and things",
            ),
            _show(
                "placeholder-six",
                "Placeholder Podcast Six",
                ["Host I"],
                "Audio and talky talky yapyap",
            ),
            _show(
                "placeholder-seven",
                "Placeholder Podcast Seven",
                ["Host J", "Host K"],
                "Piaan things",
            ),
            _show(
                "placeholder-eight",
                "Placeholder Podcast Eight",
                ["Host L"],
                "The one tirga is in!",
            ),
        ],
    },
}


def get_list(list_slug):
    return LISTS.get(list_slug)


def get_item(list_slug, item_slug):
    lst = get_list(list_slug)
    if not lst:
        return None, None
    for item in lst["items"]:
        if item["slug"] == item_slug:
            return lst, item
    return lst, None
