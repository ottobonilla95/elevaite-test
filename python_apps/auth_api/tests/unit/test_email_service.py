"""Tests for the email service module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.services.email_service import (
    send_email,
    send_password_reset_email,
    send_verification_email,
    send_welcome_email_with_temp_password,
    send_password_reset_email_with_new_password,
)


@pytest.mark.asyncio
class TestEmailFunctions:
    """Tests for the email service functions."""

    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_email_success(self, mock_smtp):
        """Test sending an email successfully."""
        # Setup mock SMTP
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        # Call function
        result = await send_email(
            recipient="user@example.com",
            subject="Test Subject",
            text_body="Test plain text",
            html_body="<p>Test HTML</p>",
        )

        # Verify result
        assert result is True

        # Verify SMTP was called
        assert mock_smtp_instance.sendmail.called

        # Check arguments
        call_args = mock_smtp_instance.sendmail.call_args
        assert len(call_args[0]) == 3  # sender, recipient, message
        assert call_args[0][1] == "user@example.com"

    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_email_failure(self, mock_smtp):
        """Test sending an email with failure."""
        # Setup mock SMTP to raise exception
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.sendmail.side_effect = smtplib.SMTPException(
            "Failed to send"
        )
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        # Call function
        result = await send_email(
            recipient="user@example.com",
            subject="Test Subject",
            text_body="Test plain text",
        )

        # Verify result
        assert result is False

    @patch("app.services.email_service.send_email")
    async def test_send_password_reset_email(self, mock_send_email):
        """Test sending a password reset email."""
        # Setup mock
        mock_send_email.return_value = True

        # Call function
        result = await send_password_reset_email(
            email="user@example.com", name="Test User", reset_token="reset-token"
        )

        # Verify send_email was called
        assert mock_send_email.called

        # Check arguments
        call_args = mock_send_email.call_args
        # First argument is the recipient email
        assert call_args[0][0] == "user@example.com"
        # Second argument is the subject
        assert call_args[0][1] == "Reset your password"
        # Third argument is the text body
        assert "reset-token" in call_args[0][2]
        # Fourth argument is the HTML body
        assert "reset-token" in call_args[0][3]

        # Verify result
        assert result is True

    @patch("app.services.email_service.send_email")
    async def test_send_verification_email(self, mock_send_email):
        """Test sending a verification email."""
        # Setup mock
        mock_send_email.return_value = True

        # Call function
        result = await send_verification_email(
            email="user@example.com",
            name="Test User",
            verification_token="verify-token",
        )

        # Verify send_email was called
        assert mock_send_email.called

        # Check arguments
        call_args = mock_send_email.call_args
        # First argument is the recipient email
        assert call_args[0][0] == "user@example.com"
        # Second argument is the subject
        assert call_args[0][1] == "Verify your email address"
        # Third argument is the text body
        assert "verify-token" in call_args[0][2]
        # Fourth argument is the HTML body
        assert "verify-token" in call_args[0][3]

        # Verify result
        assert result is True

    @patch("app.services.email_service.send_email")
    async def test_send_welcome_email_with_temp_password(self, mock_send_email):
        """Test sending a welcome email with temporary password."""
        # Setup mock
        mock_send_email.return_value = True

        # Call function
        result = await send_welcome_email_with_temp_password(
            email="user@example.com", name="Test User", temp_password="TempPass123!"
        )

        # Verify send_email was called
        assert mock_send_email.called

        # Check arguments
        call_args = mock_send_email.call_args
        # First argument is the recipient email
        assert call_args[0][0] == "user@example.com"
        # Second argument is the subject
        assert call_args[0][1] == "Welcome to ElevAIte - Your Temporary Password"
        # Third argument is the text body
        assert "TempPass123!" in call_args[0][2]
        # Fourth argument is the HTML body
        assert "TempPass123!" in call_args[0][3]

        # Verify result
        assert result is True

    @patch("app.services.email_service.send_email")
    async def test_send_password_reset_email_with_new_password(self, mock_send_email):
        """Test sending a password reset email with new password."""
        # Setup mock
        mock_send_email.return_value = True

        # Call function
        result = await send_password_reset_email_with_new_password(
            email="user@example.com", name="Test User", new_password="NewPass123!"
        )

        # Verify send_email was called
        assert mock_send_email.called

        # Check arguments
        call_args = mock_send_email.call_args
        # First argument is the recipient email
        assert call_args[0][0] == "user@example.com"
        # Second argument is the subject
        assert call_args[0][1] == "Your New Password to ElevAIte"
        # Third argument is the text body
        assert "NewPass123!" in call_args[0][2]
        # Fourth argument is the HTML body
        assert "NewPass123!" in call_args[0][3]

        # Verify result
        assert result is True
