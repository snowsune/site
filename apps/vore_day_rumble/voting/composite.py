"""
Pillow compositing for cards
copy and paste + glue from the other
pillow composites
"""

import io
import logging
import math
import os
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Card size matches the blank backdrop
CARD_SIZE = (1200, 630)
PFP_SIZE = 240
WINNER_PFP_SIZE = 320
LEFT_CENTER = (300, 200)
RIGHT_CENTER = (900, 200)
CENTER = (CARD_SIZE[0] // 2, 220)
NAME_Y = 18
WINNER_NAME_Y = 560
NAME_COLOR = (0, 0, 0)

# Prey under each fighter: equal tiles in a grid that fits the leftover box
PREY_MAX_SIZE = 88
PREY_MIN_SIZE = 24
PREY_GAP = 6
PREY_BOTTOM_PAD = 12
PREY_MAX_WIDTH = 300


def _backdrop_path():
    return (
        Path(settings.BASE_DIR)
        / "apps"
        / "vore_day_rumble"
        / "static"
        / "vore_day_rumble"
        / "backdrop.png"
    )


def _vore_tile_path():
    return (
        Path(settings.BASE_DIR)
        / "static"
        / "background"
        / "seasonal"
        / "tile_vore_day.png"
    )


def _font_dir():
    return (
        Path(settings.BASE_DIR)
        / "apps"
        / "vore_day_rumble"
        / "static"
        / "vore_day_rumble"
        / "fonts"
    )


def _load_font(size, bold=True):
    """
    Prefer fonts we ship with the app - prod slim images often have none,
    and Pillow's default bitmap font is tiny.
    """
    bundled = _font_dir() / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    candidates = [
        bundled,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    logger.warning(
        "No TTF font found - text will be tiny. Ship fonts or install fonts-dejavu-core."
    )
    return ImageFont.load_default()


@lru_cache(maxsize=1)
def _load_vore_tile():
    path = _vore_tile_path()
    if path.exists():
        return Image.open(path).convert("RGBA")
    logger.warning("Missing vore day tile at %s", path)
    return Image.new("RGBA", (60, 60), (0, 0, 0, 0))


def _load_pfp(contestant):
    """Load a contestant's pfp, or a plain placeholder."""
    if contestant and contestant.profile_picture and contestant.profile_picture.name:
        try:
            path = contestant.profile_picture.path
            if os.path.exists(path):
                return Image.open(path).convert("RGBA")
        except Exception as e:
            logger.warning("Couldn't load pfp for %s: %s", contestant, e)

    # Soft grey placeholder
    img = Image.new("RGBA", (PFP_SIZE, PFP_SIZE), (80, 80, 90, 255))
    return img


def _square_pfp(src, size=PFP_SIZE):
    """Center-crop to square, then resize. No rounded corners."""
    w, h = src.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    src = src.crop((left, top, left + side, top + side))
    return src.resize((size, size), Image.Resampling.LANCZOS)


def _prey_badge(contestant, size):
    """PFP with the vore-day jaws stamped over it."""
    pfp = _square_pfp(_load_pfp(contestant), size=size)
    jaws = _load_vore_tile().resize((size, size), Image.Resampling.LANCZOS)
    badge = pfp.copy()
    badge.alpha_composite(jaws)
    return badge


def _prey_grid_dims(count):
    """Pick columns/rows — short wide grids over tall stacks."""
    if count <= 0:
        return 0, 0
    if count == 1:
        return 1, 1
    if count == 2:
        return 2, 1
    if count <= 4:
        return 2, math.ceil(count / 2)
    if count <= 9:
        return 3, math.ceil(count / 3)
    if count <= 16:
        return 4, math.ceil(count / 4)
    cols = math.ceil(math.sqrt(count))
    return cols, math.ceil(count / cols)


def _prey_cell_size(cols, rows, max_w, max_h):
    if cols <= 0 or rows <= 0 or max_w <= 0 or max_h <= 0:
        return PREY_MIN_SIZE
    size_w = (max_w - (cols - 1) * PREY_GAP) // cols
    size_h = (max_h - (rows - 1) * PREY_GAP) // rows
    return max(PREY_MIN_SIZE, min(PREY_MAX_SIZE, size_w, size_h))


def _paste_centered(base, overlay, center):
    x = int(center[0] - overlay.width / 2)
    y = int(center[1] - overlay.height / 2)
    if overlay.mode == "RGBA":
        base.paste(overlay, (x, y), overlay)
    else:
        base.paste(overlay, (x, y))


def _paste_prey_grid(
    card, prey, center_x, start_y, max_width=PREY_MAX_WIDTH, max_bottom=None
):
    """Draw prior prey as an equal-tile grid under a fighter."""
    if not prey:
        return

    count = len(prey)
    cols, rows = _prey_grid_dims(count)
    bottom = CARD_SIZE[1] - PREY_BOTTOM_PAD if max_bottom is None else max_bottom
    available_h = bottom - start_y
    size = _prey_cell_size(cols, rows, max_width, available_h)

    for i, contestant in enumerate(prey):
        row = i // cols
        col = i % cols
        items_in_row = min(cols, count - row * cols)
        row_w = items_in_row * size + (items_in_row - 1) * PREY_GAP
        row_left = center_x - row_w // 2
        x = row_left + col * (size + PREY_GAP) + size // 2
        y = start_y + row * (size + PREY_GAP) + size // 2
        _paste_centered(card, _prey_badge(contestant, size), (x, y))


def _draw_centered_text(draw, text, center_x, y, font, fill=(255, 255, 255)):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((center_x - w / 2, y), text, font=font, fill=fill)


def _blank_card():
    backdrop_path = _backdrop_path()
    if backdrop_path.exists():
        return (
            Image.open(backdrop_path)
            .convert("RGBA")
            .resize(CARD_SIZE, Image.Resampling.LANCZOS)
        )
    return Image.new("RGBA", CARD_SIZE, (32, 32, 40, 255))


def create_matchup_image(contestant_a, contestant_b, prey_a=None, prey_b=None):
    """
    Composite two contestants onto the backdrop with names + VS.
    Optional prey_a / prey_b: prior prey newest-first, drawn underneath.
    Returns a BytesIO PNG ready to upload.
    """
    prey_a = prey_a or []
    prey_b = prey_b or []
    card = _blank_card()

    left = _square_pfp(_load_pfp(contestant_a))
    right = _square_pfp(_load_pfp(contestant_b))
    _paste_centered(card, left, LEFT_CENTER)
    _paste_centered(card, right, RIGHT_CENTER)

    trail_y = LEFT_CENTER[1] + PFP_SIZE // 2 + PREY_GAP
    _paste_prey_grid(card, prey_a, LEFT_CENTER[0], trail_y)
    _paste_prey_grid(card, prey_b, RIGHT_CENTER[0], trail_y)

    draw = ImageDraw.Draw(card)
    name_font = _load_font(48)
    vs_font = _load_font(100)

    left_name = (contestant_a.display_name if contestant_a else "-")[:28]
    right_name = (contestant_b.display_name if contestant_b else "-")[:28]

    _draw_centered_text(
        draw, left_name, LEFT_CENTER[0], NAME_Y, name_font, fill=NAME_COLOR
    )
    _draw_centered_text(
        draw, right_name, RIGHT_CENTER[0], NAME_Y, name_font, fill=NAME_COLOR
    )
    _draw_centered_text(
        draw,
        "VS",
        CARD_SIZE[0] // 2,
        CARD_SIZE[1] // 2 - 40,
        vs_font,
        fill=(255, 220, 100),
    )

    buf = io.BytesIO()
    card.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return buf


def create_winner_image(contestant, prey=None):
    """
    Single contestant centered on the backdrop with WINNER.
    Optional prey: prior prey newest-first under the champ.
    """
    prey = prey or []
    card = _blank_card()

    pfp = _square_pfp(_load_pfp(contestant), size=WINNER_PFP_SIZE)
    _paste_centered(card, pfp, CENTER)

    trail_y = CENTER[1] + WINNER_PFP_SIZE // 2 + PREY_GAP
    _paste_prey_grid(
        card,
        prey,
        CENTER[0],
        trail_y,
        max_width=min(PREY_MAX_WIDTH * 2, 420),
        max_bottom=WINNER_NAME_Y - PREY_GAP,
    )

    draw = ImageDraw.Draw(card)
    name_font = _load_font(56)
    winner_font = _load_font(96)
    name = (contestant.display_name if contestant else "-")[:28]

    _draw_centered_text(
        draw, "WINNER", CENTER[0], 40, winner_font, fill=(255, 220, 100)
    )
    _draw_centered_text(
        draw, name, CENTER[0], WINNER_NAME_Y, name_font, fill=NAME_COLOR
    )

    buf = io.BytesIO()
    card.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return buf
