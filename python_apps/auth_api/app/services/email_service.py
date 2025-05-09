import logging
import requests
from typing import Optional, Dict, List, Any, Union
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    sender: Optional[str] = None,
    sender_name: Optional[str] = None,
) -> bool:
    """
    Send an email using SendGrid API.

    Args:
        recipient: Email address of the recipient
        subject: Email subject
        text_body: Plain text email body
        html_body: HTML email body (optional)
        sender: Sender email address (defaults to settings.EMAILS_FROM_EMAIL)
        sender_name: Sender name (defaults to settings.EMAILS_FROM_NAME)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Use default sender if not provided
    sender_email = sender or settings.EMAILS_FROM_EMAIL
    from_name = sender_name or settings.EMAILS_FROM_NAME

    # Get API key from settings
    api_key = settings.SMTP_PASSWORD
    if not api_key.startswith("SG."):
        logger.error("Invalid SendGrid API key format")
        return False

    # SendGrid API endpoint
    url = "https://api.sendgrid.com/v3/mail/send"

    # Prepare headers
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Prepare email content
    email_data = {
        "personalizations": [{"to": [{"email": recipient}], "subject": subject}],
        "from": {"email": sender_email, "name": from_name},
        "content": [{"type": "text/plain", "value": text_body}],
    }

    # Add HTML content if provided
    if html_body:
        email_data["content"].append({"type": "text/html", "value": html_body})

    try:
        # Send the request to SendGrid API
        response = requests.post(url, headers=headers, json=email_data)

        # Check if the request was successful (status code 202)
        if response.status_code == 202:
            logger.info(f"Email sent to {recipient}: {subject}")
            return True
        else:
            error_msg = f"Failed to send email. Status code: {response.status_code}"
            try:
                error_details = response.json()
                error_msg += f", Response: {json.dumps(error_details)}"
            except:
                error_msg += f", Response: {response.text}"

            logger.error(error_msg)
            return False
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {str(e)}")
        return False


async def send_verification_email(
    email: str, name: str, verification_token: str
) -> bool:
    """
    Send email verification link to a new user.

    Args:
        email: User's email address
        name: User's name (first name or full name)
        verification_token: Verification token

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    verification_url = (
        f"{settings.FRONTEND_URI}/verify-email?token={verification_token}"
    )

    subject = "Verify your email address"

    text_body = f"""
    Hello {name},

    Thank you for registering with elevAIte. Please verify your email address by clicking the link below:

    {verification_url}

    This link will expire in 24 hours.

    If you did not register for an account, please ignore this email.

    Best regards,
    The elevAIte Team
    """

    html_body = f"""
    <html>
    <body>
        <h2>Welcome to elevAIte!</h2>
        <p>Hello {name},</p>
        <p>Thank you for registering with elevAIte. Please verify your email address by clicking the button below:</p>
        <p>
            <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                Verify Email
            </a>
        </p>
        <p>Or copy and paste this link in your browser: <a href="{verification_url}">{verification_url}</a></p>
        <p>This link will expire in 24 hours.</p>
        <p>If you did not register for an account, please ignore this email.</p>
        <p>Best regards,<br>The elevAIte Team</p>
    </body>
    </html>
    """

    return await send_email(email, subject, text_body, html_body)


async def send_password_reset_email(email: str, name: str, reset_token: str) -> bool:
    """
    Send password reset link to a user.

    Args:
        email: User's email address
        name: User's name (first name or full name)
        reset_token: Password reset token

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    reset_url = f"{settings.FRONTEND_URI}/reset-password?token={reset_token}"

    subject = "Reset your password"

    text_body = f"""
    Hello {name},

    We received a request to reset your password. Please click the link below to reset your password:

    {reset_url}

    This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours.

    If you did not request a password reset, please ignore this email.

    Best regards,
    The elevAIte Team
    """

    html_body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hello {name},</p>
        <p>We received a request to reset your password. Please click the button below to reset your password:</p>
        <p>
            <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                Reset Password
            </a>
        </p>
        <p>Or copy and paste this link in your browser: <a href="{reset_url}">{reset_url}</a></p>
        <p>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>Best regards,<br>The elevAIte Team</p>
    </body>
    </html>
    """

    return await send_email(email, subject, text_body, html_body)


async def send_welcome_email_with_temp_password(
    email: str, name: str, temp_password: str
) -> bool:
    """
    Send welcome email with temporary password to a new user.

    Args:
        email: User's email address
        name: User's name (first name or full name)
        temp_password: Temporary password

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    login_url = f"{settings.FRONTEND_URI}/login"

    subject = "Welcome to elevAIte - Your Temporary Password"

    text_body = f"""
    Hello {name},

    Welcome to elevAIte! Your account has been created successfully.

    Here is your temporary password: {temp_password}

    Please log in at {login_url} with this temporary password. You will be prompted to change your password after your first login.

    Best regards,
    The elevAIte Team
    """

    html_body = f"""
    <html>
    <body>
        <h2>Welcome to elevAIte!</h2>
        <p>Hello {name},</p>
        <p>Your account has been created successfully.</p>
        <p>Here is your temporary password: <strong>{temp_password}</strong></p>
        <p>Please <a href="{login_url}">log in</a> with this temporary password. You will be prompted to change your password after your first login.</p>
        <p>Best regards,<br>The elevAIte Team</p>
    </body>
    </html>
    """

    return await send_email(email, subject, text_body, html_body)


async def send_password_reset_email_with_new_password(
    email: str, name: str, new_password: str
) -> bool:
    """
    Send password reset email with a new randomized password.

    Args:
        email: User's email address
        name: User's name (first name or full name)
        new_password: The new randomized password

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    login_url = f"{settings.FRONTEND_URI}/login"

    subject = "Your Password Has Been Reset"

    text_body = f"""
    Hello {name},

    Your password has been reset as requested. Here is your new temporary password:

    {new_password}

    Please log in at {login_url} with this temporary password. You will be prompted to change your password after your first login.

    If you did not request a password reset, please contact support immediately.

    Best regards,
    The elevAIte Team
    """

    html_body = f"""
    <html>
    <body>
        <h2>Password Reset Completed</h2>
        <p>Hello {name},</p>
        <p>Your password has been reset as requested. Here is your new temporary password:</p>
        <p style="background-color: #f5f5f5; padding: 10px; font-family: monospace; font-size: 16px; border: 1px solid #ddd; border-radius: 4px;">
            {new_password}
        </p>
        <p>Please <a href="{login_url}">log in</a> with this temporary password. You will be prompted to change your password after your first login.</p>
        <p>If you did not request a password reset, please contact support immediately.</p>
        <p>Best regards,<br>The elevAIte Team</p>
    </body>
    </html>
    """

    return await send_email(email, subject, text_body, html_body)
