from PIL import Image
from io import BytesIO
from django.http import HttpResponse, Http404
from django.conf import settings
import os


def create_social_preview_image(image_path, target_ratio=1.91):
    """
    Create a social media preview image with the correct aspect ratio.

    Args:
        image_path: Path to the original image (relative to MEDIA_ROOT)
        target_ratio: Target aspect ratio (width/height). Default 1.91 (Facebook/Twitter)

    Returns:
        PIL Image object cropped to the target ratio
    """
    try:
        # Build full path to the image
        full_path = os.path.join(settings.MEDIA_ROOT, image_path.lstrip("/"))

        if not os.path.exists(full_path):
            return None

        # Open the image
        with Image.open(full_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ("RGBA", "LA", "P"):
                # Create white background for transparent images
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(
                    img, mask=img.split()[-1] if img.mode == "RGBA" else None
                )
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Calculate target dimensions
            width, height = img.size
            current_ratio = width / height

            if current_ratio > target_ratio:
                # Image is too wide, crop horizontally
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                img = img.crop((left, 0, left + new_width, height))
            elif current_ratio < target_ratio:
                # Image is too tall, crop vertically
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                img = img.crop((0, top, width, top + new_height))

            # Resize to a reasonable size for social media (1200x630 is optimal)
            target_width = 1200
            target_height = int(target_width / target_ratio)
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            return img

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None


def get_social_preview_url(original_url, target_ratio=1.91):
    """
    Convert a regular media URL to a social preview URL.

    Args:
        original_url: Original media URL (e.g., /media/blog/featured/image.jpg)
        target_ratio: Target aspect ratio

    Returns:
        Social preview URL (e.g., /format_preview/blog/featured/image.jpg)
    """
    if not original_url:
        return None

    # Remove /media/ prefix if present
    if original_url.startswith("/media/"):
        path = original_url[7:]  # Remove '/media/'
    else:
        path = original_url.lstrip("/")

    return f"/format_preview/{path}"


def format_preview_view(request, image_path):
    """
    Serve a formatted preview image with the correct aspect ratio for social media.

    URL pattern: /format_preview/blog/featured/image.jpg
    """
    try:
        # Build the full path to the original image
        original_path = os.path.join(settings.MEDIA_ROOT, image_path)

        if not os.path.exists(original_path):
            raise Http404(f"Image not found: {image_path}, searched {original_path}")

        # Create the social preview image
        preview_img = create_social_preview_image(image_path)

        if not preview_img:
            raise Http404("Could not process image")

        # Convert to bytes
        buffer = BytesIO()
        preview_img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)

        # Create response with improved caching
        response = HttpResponse(buffer.getvalue(), content_type="image/jpeg")

        # Caching for preview images (1 day)
        response["Cache-Control"] = "public, max-age=86400, immutable"
        response["Expires"] = "Thu, 31 Dec 2037 23:55:55 GMT"
        response["ETag"] = f'"{hash(image_path)}"'

        return response

    except Exception as e:
        print(f"Error serving format_preview for {image_path}: {e}")
        import traceback

        traceback.print_exc()
        raise Http404(f"Image processing error: {str(e)}")
