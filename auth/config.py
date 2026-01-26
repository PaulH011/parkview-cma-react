"""
Authentication configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///parkview.db')

# Security settings
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
BCRYPT_COST = 12  # bcrypt work factor

# Token settings
VERIFICATION_TOKEN_EXPIRY_HOURS = 24
SESSION_TOKEN_EXPIRY_DAYS = 30

# Email settings
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'Parkview CMA Tool')

# App settings
APP_URL = os.getenv('APP_URL', 'http://localhost:8501')

# Validation
MIN_PASSWORD_LENGTH = 8
