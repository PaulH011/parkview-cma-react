"""
Authentication module for Parkview CMA Tool.

Provides user authentication, email verification, and session management.
"""

from auth.middleware import require_auth, get_current_user, logout
from auth.database import init_db, get_session
from auth.models import User, Scenario, EmailVerificationToken

__all__ = [
    'require_auth',
    'get_current_user',
    'logout',
    'init_db',
    'get_session',
    'User',
    'Scenario',
    'EmailVerificationToken',
]
