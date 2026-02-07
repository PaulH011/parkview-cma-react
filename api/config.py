"""
API Configuration and Environment Variables
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# CORS Origins
_cors_origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
]

# Add production frontend URL from environment
_frontend_url = os.getenv("FRONTEND_URL", "")
if _frontend_url:
    _cors_origins.append(_frontend_url)

CORS_ORIGINS = _cors_origins

# Super User
SUPER_USER_EMAIL = os.getenv("SUPER_USER_EMAIL", "")

# Anthropic Claude (for AI-powered market research)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
