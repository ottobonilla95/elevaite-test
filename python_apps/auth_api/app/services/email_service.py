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
    """
 
    sender_email = sender or settings.EMAILS_FROM_EMAIL
    from_name = sender_name or settings.EMAILS_FROM_NAME

  
    logger.info("=" * 50)
    logger.info("EMAIL SEND ATTEMPT")
    logger.info(f"Recipient: {recipient}")
    logger.info(f"Subject: {subject}")
    logger.info(f"SMTP Host: {settings.SMTP_HOST}")
    logger.info(f"SMTP Port: {settings.SMTP_PORT}")
    logger.info(f"SMTP TLS: {settings.SMTP_TLS}")
    logger.info(f"SMTP User: {settings.SMTP_USER[:10] if settings.SMTP_USER else 'NOT SET'}***")
    logger.info(f"SMTP Password Set: {bool(settings.SMTP_PASSWORD)}")
    logger.info(f"From Email: {sender_email}")
    logger.info("=" * 50)

    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{from_name} <{sender_email}>"
    message["To"] = recipient


    message.attach(MIMEText(text_body, "plain"))

 
    if html_body:
        message.attach(MIMEText(html_body, "html"))

    try:
        # Use SSL or TLS based on settings
        if settings.SMTP_TLS:
            logger.info("Attempting TLS connection...")
            # Use TLS
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                logger.info("SMTP connection established")
                
                logger.info("Starting TLS...")
                server.starttls()
                logger.info("TLS started successfully")

                # Login if credentials are provided
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    logger.info("Attempting SMTP login...")
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    logger.info("SMTP login successful")

                # Send email
                logger.info("Sending email...")
                server.sendmail(sender_email, recipient, message.as_string())
                logger.info("Email sent successfully!")
        else:
            logger.info("Attempting SSL connection...")
            # Use SSL
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=10
            ) as server:
                logger.info("SMTP SSL connection established")
                
                # Login if credentials are provided
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    logger.info("Attempting SMTP login...")
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    logger.info("SMTP login successful")

                # Send email
                logger.info("Sending email...")
                server.sendmail(sender_email, recipient, message.as_string())
                logger.info("Email sent successfully!")

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
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error("=" * 50)
        logger.error("❌ SMTP AUTHENTICATION FAILED")
        logger.error(f"Error: {str(e)}")
        logger.error(f"SMTP User: {settings.SMTP_USER}")
        logger.error(f"SMTP Host: {settings.SMTP_HOST}")
        logger.error(f"SMTP Port: {settings.SMTP_PORT}")
        logger.error("Likely cause: Password expired or incorrect")
        logger.error("=" * 50)
        logger.error(
            f"Failed to send email to {recipient}: Authentication failed - {str(e)}",
            extra={
                "recipient": recipient,
                "subject": subject,
                "sender": sender_email,
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
                "error": str(e),
                "error_type": "SMTPAuthenticationError"
            },
        )
        return False
        
    except smtplib.SMTPConnectError as e:
        logger.error("=" * 50)
        logger.error("❌ SMTP CONNECTION FAILED")
        logger.error(f"Error: {str(e)}")
        logger.error(f"SMTP Host: {settings.SMTP_HOST}")
        logger.error(f"SMTP Port: {settings.SMTP_PORT}")
        logger.error("Likely cause: Wrong host/port or firewall blocking")
        logger.error("=" * 50)
        logger.error(
            f"Failed to send email to {recipient}: Connection failed - {str(e)}",
            extra={
                "recipient": recipient,
                "error": str(e),
                "error_type": "SMTPConnectError"
            },
        )
        return False
        
    except smtplib.SMTPException as e:
        logger.error("=" * 50)
        logger.error("❌ SMTP ERROR")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 50)
        logger.error(
            f"Failed to send email to {recipient}: SMTP error - {str(e)}",
            extra={
                "recipient": recipient,
                "subject": subject,
                "error": str(e),
                "error_type": type(e).__name__
            },
        )
        return False
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ UNEXPECTED EMAIL ERROR")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.error("Full Traceback:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        logger.error(
            f"Failed to send email to {recipient}: {str(e)}",
            extra={
                "recipient": recipient,
                "subject": subject,
                "sender": sender_email,
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
                "error": str(e),
                "error_type": type(e).__name__
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

    Thank you for registering with {settings.BRANDING_NAME}. Please verify your email address by clicking the link below:

    {verification_url}

    This link will expire in 24 hours.

    If you did not register for an account, please ignore this email.

    Best regards,
    The {settings.BRANDING_ORG} Team
    """

    html_body = f"""
    <html>
    <body>
        <h2>Welcome to {settings.BRANDING_NAME}!</h2>
        <p>Hello {name},</p>
        <p>Thank you for registering with {settings.BRANDING_NAME}. Please verify your email address by clicking the button below:</p>
        <p>
            <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                Verify Email
            </a>
        </p>
        <p>Or copy and paste this link in your browser: <a href="{verification_url}">{verification_url}</a></p>
        <p>This link will expire in 24 hours.</p>
        <p>If you did not register for an account, please ignore this email.</p>
        <p>Best regards,<br>The {settings.BRANDING_ORG} Team</p>
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
    The {settings.BRANDING_ORG} Team
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
        <p>Best regards,<br>The {settings.BRANDING_ORG} Team</p>
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
    mfa_url = f"{settings.FRONTEND_URI}/settings#mfa"

    # Get MFA settings for the email
    mfa_method = settings.MFA_AUTO_ENABLE_METHOD
    grace_period = settings.EMAIL_MFA_GRACE_PERIOD_DAYS
    primary_color = f"#{settings.MFA_EMAIL_PRIMARY_COLOR}"

    subject = f"Welcome to {settings.BRANDING_NAME} - Your Temporary Password"

    text_body = f"""
    Hello {name},

    Welcome to {settings.BRANDING_NAME}! Your account has been created successfully.

    Here is your temporary password: {temp_password}

    Please log in at {login_url} with this temporary password. You will be prompted to change your password after your first login.

    IMPORTANT SECURITY NOTICE:
    For your account security, {mfa_method.upper()} multi-factor authentication will be automatically enabled after {grace_period} days. We strongly recommend that you enable it sooner by visiting your account settings at {mfa_url} to enhance your account security immediately.

    Best regards,
    The {settings.BRANDING_NAME} Team
    """

    # Escape the password for HTML to prevent rendering issues
    escaped_password = html.escape(temp_password)

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: {primary_color}; text-align: center;">Welcome to {settings.BRANDING_NAME}!</h2>
            <p>Hello {name},</p>

            <p>Please <a href="{login_url}" style="color: {primary_color}; text-decoration: none; font-weight: bold; font-size: 18px;">log in</a> with this temporary password. You will be prompted to change your password after your first login.</p>
            
            <div style="background-color: #f8f9fa; border: 2px solid {primary_color}; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="margin: 0 0 10px 0;"><strong>Your temporary password:</strong></p>
                <div style="font-size: 24px; font-weight: bold; color: {primary_color}; letter-spacing: 2px; font-family: monospace;">
                    {escaped_password}
                </div>
            </div>

            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0;"><strong>Important Security Notice:</strong></p>
                <p style="margin: 0;">For your account security, <strong>{mfa_method.upper()}</strong> multi-factor authentication will be automatically enabled after <strong>{grace_period} days</strong>. We strongly recommend that you enable it sooner by visiting your <a href="{mfa_url}" style="color: {primary_color}; text-decoration: none; font-weight: bold;">account settings</a> to enhance your account security immediately.</p>
            </div>

            <p>Best regards,<br>The {settings.BRANDING_ORG} Team</p>
        </div>
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

You requested a new password for your {settings.BRANDING_NAME} account.

Here is your temporary password: {new_password}

Please log in at {login_url} with this temporary password. You will be prompted to change your password after your first login.

If you did not request a password reset, please ignore this email.

Best regards,
The {settings.BRANDING_ORG} Team"""

    # Escape the password for HTML to prevent rendering issues
    escaped_password = html.escape(new_password)

    html_body = f"""<html>
<body>
    <h2>Your New Password to {settings.BRANDING_NAME}</h2>
    <p>Hello {name},</p>
    <p>You requested a new password for your {settings.BRANDING_NAME} account.</p>
    <p>Here is your temporary password: <strong><code>{escaped_password}</code></strong></p>
    <p>Please <a href="{login_url}">log in</a> with this temporary password. You will be prompted to change your password after your first login.</p>
    <p>If you did not request a password reset, please ignore this email.</p>
    <p>Best regards,<br>The {settings.BRANDING_ORG} Team</p>
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

For support, please contact us at {settings.BRANDING_SUPPORT_EMAIL}

Best regards,
The {settings.BRANDING_ORG} Team"""

    html_body = f"""<html>
<body>
    <h2>Your ElevAIte Password Has Been Changed</h2>
    <p>Hello {name},</p>
    <p>Your password for ElevAIte has been successfully changed.</p>
    <p><strong>If you did not make this change, please reset your password immediately and contact support.</strong></p>
    <p>You can <a href="{reset_url}">reset your password here</a> if this change was not authorized.</p>
    <p>For support, please contact us at <a href="mailto:{settings.BRANDING_SUPPORT_EMAIL}">{settings.BRANDING_SUPPORT_EMAIL}</a></p>
    <p>Best regards,<br>The {settings.BRANDING_ORG} Team</p>
</body>
</html>"""

    return await send_email(email, subject, text_body, html_body)