"""
Email service for sending verification emails.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from auth.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_NAME, APP_URL
)

logger = logging.getLogger(__name__)


def is_email_configured() -> bool:
    """Check if email settings are configured."""
    return bool(SMTP_USER and SMTP_PASSWORD)


def send_verification_email(to_email: str, token: str) -> bool:
    """
    Send a verification email with the provided token.
    Returns True if successful, False otherwise.
    """
    if not is_email_configured():
        logger.warning("Email not configured - skipping verification email")
        return False

    verification_link = f"{APP_URL}?verify={token}"

    subject = "Verify your Parkview CMA account"

    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #1E3A5F; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #1E3A5F;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Parkview CMA Tool</h1>
            </div>
            <div class="content">
                <h2>Welcome!</h2>
                <p>Thank you for registering for the Parkview CMA Tool. Please verify your email address by clicking the button below:</p>

                <p style="text-align: center;">
                    <a href="{verification_link}" class="button">Verify Email Address</a>
                </p>

                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #1E3A5F;">{verification_link}</p>

                <p><strong>This link will expire in 24 hours.</strong></p>

                <p>If you didn't create an account, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>Parkview Capital Market Assumptions Tool</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Plain text fallback
    text_body = f"""
    Welcome to Parkview CMA Tool!

    Please verify your email address by clicking this link:
    {verification_link}

    This link will expire in 24 hours.

    If you didn't create an account, you can safely ignore this email.
    """

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        msg['To'] = to_email

        # Attach both plain text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        logger.info(f"Verification email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False


def send_password_reset_email(to_email: str, token: str) -> bool:
    """
    Send a password reset email.
    Returns True if successful, False otherwise.
    """
    if not is_email_configured():
        logger.warning("Email not configured - skipping password reset email")
        return False

    reset_link = f"{APP_URL}?reset={token}"

    subject = "Reset your Parkview CMA password"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #1E3A5F; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #1E3A5F;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Parkview CMA Tool</h1>
            </div>
            <div class="content">
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>

                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </p>

                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #1E3A5F;">{reset_link}</p>

                <p><strong>This link will expire in 24 hours.</strong></p>

                <p>If you didn't request a password reset, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>Parkview Capital Market Assumptions Tool</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Password Reset Request

    We received a request to reset your password. Click this link to create a new password:
    {reset_link}

    This link will expire in 24 hours.

    If you didn't request a password reset, you can safely ignore this email.
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        msg['To'] = to_email

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        logger.info(f"Password reset email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False
