import asyncio
from unittest.mock import patch

from app.services.email_service import send_password_reset_email_with_new_password


class TestPasswordResetEmail:
    """Tests for password reset email functionality."""

    @patch("app.services.email_service.send_email")
    def test_send_password_reset_email_with_new_password(self, mock_send_email):
        """Test that send_password_reset_email_with_new_password sends the correct email."""
        # Setup mock
        mock_send_email.return_value = True

        # Call the function
        email = "test@example.com"
        name = "Test"
        new_password = "NewSecurePassword123!@#"

        # Run the async function in a synchronous context
        result = asyncio.run(
            send_password_reset_email_with_new_password(email, name, new_password)
        )

        # Check that send_email was called with the correct arguments
        assert mock_send_email.called
        call_args = mock_send_email.call_args[0]

        # Check recipient
        assert call_args[0] == email

        # Check subject aligns with current implementation
        assert call_args[1] == "Your New Password to ElevAIte"

        # Check that the email body contains the name and password
        assert name in call_args[2]  # Text body
        assert new_password in call_args[2]  # Text body
        assert name in call_args[3]  # HTML body
        assert new_password in call_args[3]  # HTML body

        # Check result
        assert result is True
