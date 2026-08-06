"""
Pillow compositing for cards
copy and paste + glue from the other
pillow composites
"""

import io
import logging
import os
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Card size matches the blank backdrop
CARD_SIZE = (1200, 630)
PFP_SIZE = 280
WINNER_PFP_SIZE = 360
LEFT_CENTER = (320, 260)
RIGHT_CENTER = (880, 260)
CENTER = (CARD_SIZE[0] // 2, 300)
NAME_Y = 470
WINNER_NAME_Y = 530
NAME_COLOR = (0, 0, 0)


def _backdrop_path():
    return (
        Path(settings.BASE_DIR)
        / "apps"
        / "vore_day_rumble"
        / "static"
        / "vore_day_rumble"
        / "backdrop.png"
    )


def _load_font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


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


def _paste_centered(base, overlay, center):
    x = int(center[0] - overlay.width / 2)
    y = int(center[1] - overlay.height / 2)
    if overlay.mode == "RGBA":
        base.paste(overlay, (x, y), overlay)
    else:
        base.paste(overlay, (x, y))


def _draw_centered_text(draw, text, center_x, y, font, fill=(255, 255, 255)):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((center_x - w / 2, y), text, font=font, fill=fill)


def create_matchup_image(contestant_a, contestant_b):
    """
    Composite two contestants onto the backdrop with names + VS.
    Returns a BytesIO PNG ready to upload.
    """
    backdrop_path = _backdrop_path()
    if backdrop_path.exists():
        card = Image.open(backdrop_path).convert("RGBA").resize(
            CARD_SIZE, Image.Resampling.LANCZOS
        )
    else:
        card = Image.new("RGBA", CARD_SIZE, (32, 32, 40, 255))

    left = _square_pfp(_load_pfp(contestant_a))
    right = _square_pfp(_load_pfp(contestant_b))
    _paste_centered(card, left, LEFT_CENTER)
    _paste_centered(card, right, RIGHT_CENTER)

    draw = ImageDraw.Draw(card)
    name_font = _load_font(36)
    vs_font = _load_font(72)

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


def create_winner_image(contestant):
    """
    Single contestant centered on the backdrop with WINNER
    """
    backdrop_path = _backdrop_path()
    if backdrop_path.exists():
        card = Image.open(backdrop_path).convert("RGBA").resize(
            CARD_SIZE, Image.Resampling.LANCZOS
        )
    else:
        card = Image.new("RGBA", CARD_SIZE, (32, 32, 40, 255))

    pfp = _square_pfp(_load_pfp(contestant), size=WINNER_PFP_SIZE)
    _paste_centered(card, pfp, CENTER)

    draw = ImageDraw.Draw(card)
    name_font = _load_font(40)
    winner_font = _load_font(80)
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
