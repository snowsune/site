import secrets
import hashlib
from urllib.parse import urlparse

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def hash_token(token):
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def send_verification_email(user):
    """
    Send an email verification message to the user.

    Args:
        user: CustomUser instance to send verification email to

    Returns:
        True if email was sent successfully, False otherwise
    """
    if not user.email:
        logger.warning(f"User {user.username} has no email address set")
        return False

    # Generate a new verification token
    token = generate_verification_token()
    user.email_verification_token = hash_token(token)
    user.email_verification_sent_at = timezone.now()
    user.email_verified = False  # Ensure they're unverified
    user.save()

    # Create verification link (always canonical origin, not dev SITE_URL)
    base = settings.EMAIL_VERIFICATION_CANONICAL_ORIGIN.rstrip("/")
    path = reverse("verify-email", kwargs={"user_id": user.id, "token": token})
    verification_url = f"{base}{path}"

    # Send email
    try:
        parsed_url = urlparse(settings.EMAIL_VERIFICATION_CANONICAL_ORIGIN)
        site_domain = parsed_url.netloc or parsed_url.path or "snowsune.net"

        subject = f"Verify your email address on {site_domain}"

        # You could make this a proper template later
        message = f"""Heyy {user.first_name or user.username}!

Use the following link to verify your email address:

{verification_url}

If you didn't request this verification, you can safely ignore this email.

Thanks!
- Vixi <3
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Verification email sent to {user.email} for user {user.username}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def verify_email_token(user, token):
    """
    Verify an email verification token for a user.

    Args:
        user: CustomUser instance
        token: The verification token to check

    Returns:
        True if token is valid, False otherwise
    """
    if not user.email_verification_token:
        logger.warning(f"User {user.username} has no verification token")
        return False

    # Check if token matches
    token_hash = hash_token(token)
    if user.email_verification_token != token_hash:
        logger.warning(f"Invalid verification token for user {user.username}")
        return False

    # Token is valid!
    user.email_verified = True
    user.email_verification_token = None  # Clear the token after use
    user.save()

    logger.info(f"Email verified for user {user.username}")
    return True
