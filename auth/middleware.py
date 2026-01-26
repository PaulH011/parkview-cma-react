"""
Authentication middleware for Streamlit.

Provides require_auth() to protect pages and authentication UI components.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Tuple
import json

from auth.database import get_session, init_db
from auth.models import User, EmailVerificationToken, PasswordResetToken, Scenario
from auth.security import (
    hash_password, verify_password,
    generate_verification_token, get_token_expiry,
    validate_password_strength, validate_email
)
from auth.email_service import send_verification_email, send_password_reset_email, is_email_configured


def get_current_user() -> Optional[dict]:
    """Get the current logged-in user from session state."""
    return st.session_state.get('user', None)


def logout():
    """Log out the current user."""
    if 'user' in st.session_state:
        del st.session_state['user']
    # Clear any user-specific session data
    keys_to_clear = [k for k in st.session_state.keys()
                     if k.startswith(('macro_', 'bonds_', 'equity_', 'absolute_return_', 'selected_scenario'))]
    for key in keys_to_clear:
        del st.session_state[key]


def _check_verification_token() -> Tuple[bool, Optional[Tuple[str, str]]]:
    """
    Check for email verification token in URL and process it.
    Returns (has_token, message) where message is (type, text) to display.
    Does not call any st.* display functions.
    """
    query_params = st.query_params
    verify_token = query_params.get('verify', None)

    if not verify_token:
        return False, None

    message = None

    with get_session() as session:
        token = session.query(EmailVerificationToken).filter_by(token=verify_token).first()

        if token and not token.is_used and not token.is_expired:
            # Mark token as used
            token.used_at = datetime.utcnow()

            # Mark user as verified
            user = session.query(User).filter_by(id=token.user_id).first()
            if user:
                user.is_verified = True
                session.commit()
                message = ("success", "Email verified successfully! You can now log in.")
        elif token and token.is_expired:
            message = ("error", "This verification link has expired. Please request a new one.")
        elif token and token.is_used:
            message = ("info", "This email has already been verified. Please log in.")
        else:
            message = ("error", "Invalid verification link.")

    # Clear the query parameter
    st.query_params.clear()

    return True, message


def _show_verification_message(message: Optional[Tuple[str, str]]):
    """Display a verification message if present."""
    if message:
        msg_type, msg_text = message
        if msg_type == "success":
            st.success(msg_text)
        elif msg_type == "error":
            st.error(msg_text)
        elif msg_type == "info":
            st.info(msg_text)


def _show_login_form():
    """Display the login form."""
    st.markdown("### Login")

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter email and password")
                return

            clean_email = email.lower().strip()
            
            with get_session() as session:
                user = session.query(User).filter_by(email=clean_email).first()

                if not user:
                    st.error("Invalid email or password")
                    return
                
                if verify_password(password, user.password_hash):
                    # Update last login
                    user.last_login = datetime.utcnow()
                    session.commit()

                    # Store user in session
                    st.session_state['user'] = user.to_dict()
                    st.rerun()
                else:
                    st.error("Invalid email or password")


def _show_register_form():
    """Display the registration form."""
    st.markdown("### Create Account")

    with st.form("register_form"):
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password",
                                help="At least 8 characters with letters and numbers")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            # Validate email
            is_valid, error = validate_email(email)
            if not is_valid:
                st.error(error)
                return

            # Validate password
            is_valid, error = validate_password_strength(password)
            if not is_valid:
                st.error(error)
                return

            # Check passwords match
            if password != confirm_password:
                st.error("Passwords do not match")
                return

            email = email.lower().strip()

            with get_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter_by(email=email).first()
                if existing_user:
                    st.error("An account with this email already exists")
                    return

                # Create user
                password_hash = hash_password(password)
                user = User(
                    email=email,
                    password_hash=password_hash,
                    is_verified=not is_email_configured()  # Auto-verify if email not configured
                )
                session.add(user)
                session.flush()  # Get user ID

                # Create verification token
                if is_email_configured():
                    token = EmailVerificationToken(
                        user_id=user.id,
                        token=generate_verification_token(),
                        expires_at=get_token_expiry()
                    )
                    session.add(token)
                    session.commit()

                    # Send verification email
                    if send_verification_email(email, token.token):
                        st.success("Account created! Please check your email to verify your account.")
                    else:
                        st.warning("Account created but we couldn't send the verification email. Please contact support.")
                else:
                    session.commit()
                    st.success("Account created! You can now log in.")
                    st.info("Note: Email verification is disabled. Configure SMTP settings for production use.")


def _show_resend_verification():
    """Show option to resend verification email."""
    st.markdown("---")
    st.markdown("### Resend Verification Email")

    with st.form("resend_form"):
        email = st.text_input("Email", key="resend_email")
        submitted = st.form_submit_button("Resend Verification", use_container_width=True)

        if submitted:
            if not email:
                st.error("Please enter your email")
                return

            email = email.lower().strip()

            with get_session() as session:
                user = session.query(User).filter_by(email=email).first()

                if not user:
                    st.error("No account found with this email")
                    return

                if user.is_verified:
                    st.info("This account is already verified. Please log in.")
                    return

                # Create new verification token
                token = EmailVerificationToken(
                    user_id=user.id,
                    token=generate_verification_token(),
                    expires_at=get_token_expiry()
                )
                session.add(token)
                session.commit()

                if send_verification_email(email, token.token):
                    st.success("Verification email sent! Please check your inbox.")
                else:
                    st.error("Failed to send verification email. Please try again later.")


def _check_password_reset_token() -> Tuple[bool, Optional[str], Optional[Tuple[str, str]]]:
    """
    Check for password reset token in URL.
    Returns (has_token, token_value, message).
    """
    query_params = st.query_params
    reset_token = query_params.get('reset', None)

    if not reset_token:
        return False, None, None

    # Validate the token without using it
    with get_session() as session:
        token = session.query(PasswordResetToken).filter_by(token=reset_token).first()

        if not token:
            st.query_params.clear()
            return True, None, ("error", "Invalid password reset link.")
        elif token.is_expired:
            st.query_params.clear()
            return True, None, ("error", "This password reset link has expired. Please request a new one.")
        elif token.is_used:
            st.query_params.clear()
            return True, None, ("info", "This password reset link has already been used.")

    return True, reset_token, None


def _show_forgot_password_form():
    """Display the forgot password form."""
    st.markdown("### Forgot Password")
    st.caption("Enter your email address and we'll send you a link to reset your password.")

    with st.form("forgot_password_form"):
        email = st.text_input("Email", key="forgot_email")
        submitted = st.form_submit_button("Send Reset Link", use_container_width=True)

        if submitted:
            if not email:
                st.error("Please enter your email")
                return

            email = email.lower().strip()

            with get_session() as session:
                user = session.query(User).filter_by(email=email).first()

                if not user:
                    # Don't reveal if email exists - security best practice
                    st.success("If an account with this email exists, you will receive a password reset link.")
                    return

                # Create password reset token
                token = PasswordResetToken(
                    user_id=user.id,
                    token=generate_verification_token(),
                    expires_at=get_token_expiry()
                )
                session.add(token)
                session.commit()

                if send_password_reset_email(email, token.token):
                    st.success("If an account with this email exists, you will receive a password reset link.")
                else:
                    st.error("Failed to send email. Please try again later.")


def _show_password_reset_form(reset_token: str):
    """Display the password reset form."""
    st.markdown("### Reset Your Password")
    st.caption("Enter your new password below.")

    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password", key="reset_new_password",
                                     help="At least 8 characters with letters and numbers")
        confirm_password = st.text_input("Confirm Password", type="password", key="reset_confirm_password")
        submitted = st.form_submit_button("Reset Password", use_container_width=True)

        if submitted:
            # Validate password
            is_valid, error = validate_password_strength(new_password)
            if not is_valid:
                st.error(error)
                return

            # Check passwords match
            if new_password != confirm_password:
                st.error("Passwords do not match")
                return

            with get_session() as session:
                token = session.query(PasswordResetToken).filter_by(token=reset_token).first()

                if not token or token.is_expired or token.is_used:
                    st.error("Invalid or expired reset link. Please request a new one.")
                    return

                # Update user password
                user = session.query(User).filter_by(id=token.user_id).first()
                if user:
                    user.password_hash = hash_password(new_password)
                    token.used_at = datetime.utcnow()
                    session.commit()

                    # Clear the query parameter
                    st.query_params.clear()

                    st.success("Password reset successfully! You can now log in with your new password.")
                    st.info("Please go to the Login tab to sign in.")
                else:
                    st.error("User not found. Please contact support.")


def _show_verification_required():
    """Show message when user needs to verify their email."""
    user = st.session_state.get('user', {})

    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>Please Verify Your Email</h2>
        <p style="color: #666;">
            We've sent a verification link to <strong>{email}</strong>.<br/>
            Please check your inbox and click the link to verify your account.
        </p>
    </div>
    """.format(email=user.get('email', 'your email')), unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Resend Verification Email", use_container_width=True):
            with get_session() as session:
                # Create new verification token
                token = EmailVerificationToken(
                    user_id=user['id'],
                    token=generate_verification_token(),
                    expires_at=get_token_expiry()
                )
                session.add(token)
                session.commit()

                if send_verification_email(user['email'], token.token):
                    st.success("Verification email sent!")
                else:
                    st.error("Failed to send email. Please try again.")

    with col2:
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()


def show_auth_page(verification_message: Optional[Tuple[str, str]] = None, 
                   reset_token: Optional[str] = None,
                   reset_message: Optional[Tuple[str, str]] = None):
    """Display the full authentication page with login/register tabs."""
    st.set_page_config(
        page_title="Login - Parkview CMA Tool",
        page_icon="🔐",
        layout="centered"
    )

    # Show verification message if present (from URL token check)
    _show_verification_message(verification_message)
    _show_verification_message(reset_message)

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #1E3A5F;">Parkview CMA Tool</h1>
        <p style="color: #666;">Capital Market Assumptions</p>
    </div>
    """, unsafe_allow_html=True)

    # If we have a valid reset token, show password reset form
    if reset_token:
        _show_password_reset_form(reset_token)
        st.markdown("---")
        if st.button("← Back to Login"):
            st.query_params.clear()
            st.rerun()
        return

    # Auth tabs
    if is_email_configured():
        tab_login, tab_register, tab_forgot = st.tabs(["Login", "Create Account", "Forgot Password"])
    else:
        tab_login, tab_register = st.tabs(["Login", "Create Account"])
        tab_forgot = None

    with tab_login:
        _show_login_form()

    with tab_register:
        _show_register_form()
        if is_email_configured():
            _show_resend_verification()

    if tab_forgot:
        with tab_forgot:
            _show_forgot_password_form()


def require_auth():
    """
    Require authentication to access the page.

    Call this at the top of any page that requires login.
    Returns the current user dict if authenticated, otherwise shows auth page and stops.
    """
    # Initialize database
    init_db()

    # Check for verification token in URL (before any UI)
    # This doesn't display anything yet, just processes the token
    has_verify_token, verification_message = _check_verification_token()

    # Check for password reset token in URL
    has_reset_token, reset_token, reset_message = _check_password_reset_token()

    # Check if user is logged in
    if 'user' not in st.session_state:
        # Show auth page (which sets page_config first, then shows any messages)
        show_auth_page(verification_message, reset_token, reset_message)
        st.stop()

    user = st.session_state['user']

    # Refresh user verification status from database if we had a token
    if has_verify_token and verification_message and verification_message[0] == "success":
        with get_session() as session:
            db_user = session.query(User).filter_by(id=user['id']).first()
            if db_user:
                st.session_state['user'] = db_user.to_dict()
                user = st.session_state['user']

    # Check if email is verified (only if email is configured)
    if is_email_configured() and not user.get('is_verified'):
        st.set_page_config(
            page_title="Verify Email - Parkview CMA Tool",
            page_icon="📧",
            layout="centered"
        )
        # Show any verification message first
        _show_verification_message(verification_message)
        _show_verification_required()
        st.stop()

    return user


# =============================================================================
# Scenario Management Functions (Database-backed)
# =============================================================================

def load_scenarios(user_id: str) -> dict:
    """Load saved scenarios for a specific user from database."""
    scenarios = {}
    with get_session() as session:
        user_scenarios = session.query(Scenario).filter_by(user_id=user_id).all()
        for scenario in user_scenarios:
            scenarios[scenario.name] = scenario.to_dict()
    return scenarios


def save_scenario(user_id: str, name: str, overrides: dict, base_currency: str) -> bool:
    """Save a scenario for a user to database."""
    try:
        with get_session() as session:
            # Check if scenario with this name already exists for user
            existing = session.query(Scenario).filter_by(
                user_id=user_id,
                name=name
            ).first()

            overrides_json = json.dumps(overrides)

            if existing:
                # Update existing scenario
                existing.overrides = overrides_json
                existing.base_currency = base_currency
                existing.updated_at = datetime.utcnow()
            else:
                # Create new scenario
                scenario = Scenario(
                    user_id=user_id,
                    name=name,
                    base_currency=base_currency,
                    overrides=overrides_json
                )
                session.add(scenario)

            session.commit()
            return True
    except Exception as e:
        print(f"Error saving scenario: {e}")
        return False


def delete_scenario(user_id: str, name: str) -> bool:
    """Delete a scenario owned by the user."""
    try:
        with get_session() as session:
            scenario = session.query(Scenario).filter_by(
                user_id=user_id,
                name=name
            ).first()

            if scenario:
                session.delete(scenario)
                session.commit()
                return True
            return False
    except Exception as e:
        print(f"Error deleting scenario: {e}")
        return False
