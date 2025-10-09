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
    encoded_key = base64.urlsafe_b64encode(key)
    return encoded_key


def encrypt_token(token):
    """Encrypt a Discord token for storage"""
    if not token:
        return None

    # Skip encryption in DEBUG mode to avoid SECRET_KEY mismatch between environments
    # This wouldn't be safe in prod but its going to be okay here!
    if settings.DEBUG:
        return token

    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(token.encode()).decode()
        return encrypted
    except Exception as e:
        return None


def decrypt_token(encrypted_token):
    """Decrypt a Discord token from storage"""
    if not encrypted_token:
        return None

    # Skip decryption in DEBUG mode to avoid SECRET_KEY mismatch between environments
    # This wouldn't be safe in prod but its going to be okay here!
    if settings.DEBUG:
        return encrypted_token

    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_token.encode()).decode()
        return decrypted
    except Exception as e:
        return None
