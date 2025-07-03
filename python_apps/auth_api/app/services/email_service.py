import smtplib
import ssl
import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, List, Any, Union

from app.core.config import settings
from app.core.logging import logger


async def send_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    sender: Optional[str] = None,
    sender_name: Optional[str] = None,
) -> bool:
    """
    Send an email using SMTP.

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

    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{from_name} <{sender_email}>"
    message["To"] = recipient

    # Add text body
    message.attach(MIMEText(text_body, "plain"))

    # Add HTML body if provided
    if html_body:
        message.attach(MIMEText(html_body, "html"))

    try:
        # Use SSL or TLS based on settings
        if settings.SMTP_TLS:
            # Use TLS
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()

                # Login if credentials are provided
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                # Send email
                server.sendmail(sender_email, recipient, message.as_string())
        else:
            # Use SSL
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST, settings.SMTP_PORT, context=context
            ) as server:
                # Login if credentials are provided
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                # Send email
                server.sendmail(sender_email, recipient, message.as_string())

        logger.info(
            f"Email sent to {recipient}: {subject}",
            extra={
                "recipient": recipient,
                "subject": subject,
                "sender": sender_email,
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
            },
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to send email to {recipient}: {str(e)}",
            extra={
                "recipient": recipient,
                "subject": subject,
                "sender": sender_email,
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
                "error": str(e),
            },
        )
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

    Thank you for registering with ElevAIte. Please verify your email address by clicking the link below:

    {verification_url}

    This link will expire in 24 hours.

    If you did not register for an account, please ignore this email.

    Best regards,
    The iOPEX Team
    """

    html_body = f"""
    <html>
    <body>
        <h2>Welcome to ElevAIte!</h2>
        <p>Hello {name},</p>
        <p>Thank you for registering with ElevAIte. Please verify your email address by clicking the button below:</p>
        <p>
            <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                Verify Email
            </a>
        </p>
        <p>Or copy and paste this link in your browser: <a href="{verification_url}">{verification_url}</a></p>
        <p>This link will expire in 24 hours.</p>
        <p>If you did not register for an account, please ignore this email.</p>
        <p>Best regards,<br>The iOPEX Team</p>
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
    The iOPEX Team
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
        <p>Best regards,<br>The iOPEX Team</p>
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

    subject = "Welcome to ElevAIte - Your Temporary Password"

    text_body = f"""
    Hello {name},

    Welcome to ElevAIte! Your account has been created successfully.

    Here is your temporary password: {temp_password}

    Please log in at {login_url} with this temporary password. You will be prompted to change your password after your first login.

    Best regards,
    The iOPEX Team
    """

    # Escape the password for HTML to prevent rendering issues
    escaped_password = html.escape(temp_password)

    html_body = f"""
    <html>
    <body>
        <h2>Welcome to ElevAIte!</h2>
        <p>Hello {name},</p>
        <p>Your account has been created successfully.</p>
        <p>Here is your temporary password: <strong><code>{escaped_password}</code></strong></p>
        <p>Please <a href="{login_url}">log in</a> with this temporary password. You will be prompted to change your password after your first login.</p>
        <p>Best regards,<br>The iOPEX Team</p>
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

    subject = "Your New Password to ElevAIte"

    text_body = f"""Hello {name},

You requested a new password for your ElevAIte account.

Here is your temporary password: {new_password}

Please log in at {login_url} with this temporary password. You will be prompted to change your password after your first login.

If you did not request a password reset, please ignore this email.

Best regards,
The iOPEX Team"""

    # Escape the password for HTML to prevent rendering issues
    escaped_password = html.escape(new_password)

    html_body = f"""<html>
<body>
    <h2>Your New Password to ElevAIte</h2>
    <p>Hello {name},</p>
    <p>You requested a new password for your ElevAIte account.</p>
    <p>Here is your temporary password: <strong><code>{escaped_password}</code></strong></p>
    <p>Please <a href="{login_url}">log in</a> with this temporary password. You will be prompted to change your password after your first login.</p>
    <p>If you did not request a password reset, please ignore this email.</p>
    <p>Best regards,<br>The iOPEX Team</p>
</body>
</html>"""

    return await send_email(email, subject, text_body, html_body)


async def send_password_changed_notification(email: str, name: str) -> bool:
    """
    Send password change notification to a user.

    Args:
        email: User's email address
        name: User's name (first name or full name)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    reset_url = f"{settings.FRONTEND_URI}/forgot-password"

    subject = "Your ElevAIte Password Has Been Changed"

    text_body = f"""Hello {name},

Your password for ElevAIte has been successfully changed.

If you did not make this change, please reset your password immediately and contact support.

You can reset your password at: {reset_url}

For support, please contact us at support@iopex.com

Best regards,
The iOPEX Team"""

    html_body = f"""<html>
<body>
    <h2>Your ElevAIte Password Has Been Changed</h2>
    <p>Hello {name},</p>
    <p>Your password for ElevAIte has been successfully changed.</p>
    <p><strong>If you did not make this change, please reset your password immediately and contact support.</strong></p>
    <p>You can <a href="{reset_url}">reset your password here</a> if this change was not authorized.</p>
    <p>For support, please contact us at <a href="mailto:support@iopex.com">support@iopex.com</a></p>
    <p>Best regards,<br>The iOPEX Team</p>
</body>
</html>"""

    return await send_email(email, subject, text_body, html_body)
