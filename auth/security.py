"""
Security utilities for password hashing and token generation.
"""

import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta

from auth.config import BCRYPT_COST, VERIFICATION_TOKEN_EXPIRY_HOURS


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=BCRYPT_COST)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def generate_verification_token() -> str:
    """Generate a secure random token for email verification."""
    # Generate 32 random bytes and convert to hex (64 characters)
    return secrets.token_hex(32)


def get_token_expiry() -> datetime:
    """Get the expiry datetime for a new verification token."""
    return datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets minimum requirements.
    Returns (is_valid, error_message).
    """
    from auth.config import MIN_PASSWORD_LENGTH

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)

    if not has_letter:
        return False, "Password must contain at least one letter"

    if not has_number:
        return False, "Password must contain at least one number"

    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Basic email validation.
    Returns (is_valid, error_message).
    """
    if not email or '@' not in email:
        return False, "Please enter a valid email address"

    # Basic format check
    parts = email.split('@')
    if len(parts) != 2:
        return False, "Please enter a valid email address"

    local, domain = parts
    if not local or not domain or '.' not in domain:
        return False, "Please enter a valid email address"

    return True, ""
