from cryptography.fernet import Fernet
from django.conf import settings
import hashlib
import base64


def get_encryption_key():
    """Generate encryption key from Django SECRET_KEY"""
    # Uses Django's SECRET_KEY to create a consistent encryption key
    secret = settings.SECRET_KEY.encode("utf-8")
    # Hash the secret key to get a 32-byte key for Fernet
    key = hashlib.sha256(secret).digest()
    # Encode as base64 for Fernet
    return base64.urlsafe_b64encode(key)


def encrypt_token(token):
    """Encrypt a Discord token for storage"""
    if not token:
        return None
    f = Fernet(get_encryption_key())
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token):
    """Decrypt a Discord token from storage"""
    if not encrypted_token:
        return None
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_token.encode()).decode()
    except Exception:
        return None
