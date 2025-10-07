import pytest
from unittest.mock import patch

from app.core.password_utils import generate_secure_password, is_password_temporary
from app.services.email_service import send_password_reset_email_with_new_password


class TestPasswordUtils:
    """Tests for password utility functions."""

    def test_generate_secure_password(self):
        """Test that generate_secure_password creates a secure password."""
        # Generate a password with default length
        password = generate_secure_password()

        # Check length
        assert len(password) == 16

        # Check that it contains at least one lowercase letter
        assert any(c.islower() for c in password)

        # Check that it contains at least one uppercase letter
        assert any(c.isupper() for c in password)

        # Check that it contains at least one digit
        assert any(c.isdigit() for c in password)

        # Check that it contains at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert any(c in special_chars for c in password)

        # Generate a password with custom length
        custom_length = 24
        password = generate_secure_password(custom_length)
        assert len(password) == custom_length

    def test_is_password_temporary(self):
        """Test that is_password_temporary correctly identifies test credentials."""
        # Test with test credentials
        is_test, message = is_password_temporary(
            "panagiotis.v@iopex.com", "password123"
        )
        assert is_test is True
        assert message == "Test account detected. Redirecting to password reset flow."

        # Test with regular credentials
        is_test, message = is_password_temporary(
            "regular@example.com", "regularpassword"
        )
        assert is_test is False
        assert message == ""


@pytest.mark.asyncio
class TestPasswordResetEmail:
    """Tests for password reset email functionality."""

    @patch("app.services.email_service.send_email")
    async def test_send_password_reset_email_with_new_password(self, mock_send_email):
        """Test that send_password_reset_email_with_new_password sends the correct email."""
        # Setup mock
        mock_send_email.return_value = True

        # Call the function
        email = "test@example.com"
        name = "Test"
        new_password = "NewSecurePassword123!@#"
        result = await send_password_reset_email_with_new_password(
            email, name, new_password
        )

        # Check that send_email was called with the correct arguments
        assert mock_send_email.called
        call_args = mock_send_email.call_args[0]

        # Check recipient
        assert call_args[0] == email

        # Check subject
        assert call_args[1] == "Your Password Has Been Reset"

        # Check that the email body contains the name and password
        assert name in call_args[2]  # Text body
        assert new_password in call_args[2]  # Text body
        assert name in call_args[3]  # HTML body
        assert new_password in call_args[3]  # HTML body

        # Check result
        assert result is True
