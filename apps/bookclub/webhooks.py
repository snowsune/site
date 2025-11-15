import logging
import io
import os
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.contrib.auth import get_user_model
from snowsune.models import SiteSetting

from .models import MonthlyComic, UserProgress

User = get_user_model()
logger = logging.getLogger(__name__)


def create_leader_image(user, page_number):
    """
    Should make a bytesio image using pillow

    This is clunky but in python its kinda fun to composite images by paw this way!
    """

    # Get the current comic to calculate progress
    comic = MonthlyComic.objects.first()
    if not comic:
        return None

    # Calculate progress percentage
    progress = UserProgress.objects.filter(user=user).first()
    if not progress:
        return None

    percentage = progress.get_position_percentage(comic.start_page, comic.end_page)

    # Load profile picture or default
    profile_img = None
    if user.profile_picture and user.profile_picture.name:
        try:
            profile_path = user.profile_picture.path
            if os.path.exists(profile_path):
                profile_img = Image.open(profile_path).convert("RGBA")
        except Exception as e:
            logger.warning(f"Could not load profile picture for {user.username}: {e}")

    # Use default if no profile picture
    if not profile_img:
        default_path = (
            Path(settings.BASE_DIR) / "static" / "stickers" / "foxi-sticker-ERROR.png"
        )
        if default_path.exists():
            profile_img = Image.open(str(default_path)).convert("RGBA")
        else:
            # Create a simple placeholder if default doesn't exist
            profile_img = Image.new("RGBA", (128, 128), (200, 200, 200, 255))

    # Resize profile picture to a square (128x128)
    profile_img = profile_img.resize((128, 128), Image.Resampling.LANCZOS)

    # Create a circular mask for the profile picture
    mask = Image.new("L", (128, 128), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse([0, 0, 128, 128], fill=255)

    # Apply mask to profile picture
    profile_img.putalpha(mask)

    # Create the composite image (profile + progress bar)
    # Image will be: profile (128x128) + rectangle with text (300x128)
    img_width = 128 + 300
    img_height = 128
    composite = Image.new("RGB", (img_width, img_height), (40, 40, 40))

    # Paste profile picture on the left
    composite.paste(profile_img, (0, 0), profile_img)

    # Draw progress rectangle on the right
    draw = ImageDraw.Draw(composite)

    # Background rectangle
    rect_x = 140
    rect_y = 20
    rect_width = 280
    rect_height = 88
    draw.rounded_rectangle(
        [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height],
        radius=10,
        fill=(60, 60, 60),
        outline=(200, 200, 200),
        width=2,
    )

    # Progress bar background
    bar_x = rect_x + 20
    bar_y = rect_y + 50
    bar_width = rect_width - 40
    bar_height = 20
    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
        radius=5,
        fill=(110, 110, 110),
    )

    # Progress bar fill
    fill_width = int((bar_width * percentage) / 100)
    if fill_width > 0:
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + fill_width, bar_y + bar_height],
            radius=5,
            fill=(0, 188, 212),  # Cyan color
        )

    # Try to load a font, fallback to default if not available
    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16
        )
    except:
        try:
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    # Draw username
    username_text = user.username[:20]  # Truncate if too long
    draw.text(
        (rect_x + 20, rect_y + 10),
        username_text,
        fill=(255, 255, 255),
        font=font_large,
    )

    # Draw percentage text
    percentage_text = f"{percentage}%"
    text_bbox = draw.textbbox((0, 0), percentage_text, font=font_small)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text(
        (bar_x + bar_width - text_width - 5, bar_y - 20),
        percentage_text,
        fill=(255, 255, 255),
        font=font_small,
    )

    # Convert to bytes
    img_bytes = io.BytesIO()
    composite.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


def send_leader_change_webhook(new_leader_username, new_leader_page):
    """
    Sends a webhook notification when the book club leader changes.

    (assuming i set the BOOK_CLUB_WEBHOOK site setting)
    """

    try:
        webhook_setting = SiteSetting.objects.filter(key="BOOK_CLUB_WEBHOOK").first()
        if not webhook_setting or not webhook_setting.value:
            return  # No webhook configured oops

        webhook_url = webhook_setting.value.strip()
        if not webhook_url:
            return

        # Get the user object
        try:
            user = User.objects.get(username=new_leader_username)
        except User.DoesNotExist:
            logger.error(f"User {new_leader_username} not found for webhook")
            return

        # Create the leader image
        img_bytes = create_leader_image(user, new_leader_page)
        if not img_bytes:
            logger.warning("Could not create leader image, sending text-only webhook")
            message = (
                f"{new_leader_username} is now in the lead at page {new_leader_page}!~"
            )
            payload = {"content": message}
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            return

        # Send webhook with image
        message = (
            f"{new_leader_username} is now in the lead at page {new_leader_page}!~"
        )

        # Fingers crossed attach the data manually without having to save and load
        files = {"file": ("leader.png", img_bytes, "image/png")}
        data = {"content": message}

        response = requests.post(webhook_url, data=data, files=files, timeout=10)
        response.raise_for_status()
        logger.info(f"Sent leader change webhook with image for {new_leader_username}")
    except Exception as e:
        logger.error(f"Failed to send book club leader change webhook: {e}")
