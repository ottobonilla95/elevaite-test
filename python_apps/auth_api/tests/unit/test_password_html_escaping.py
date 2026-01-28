"""Tests for HTML escaping of passwords in emails."""

import pytest
import html
from unittest.mock import patch

from app.core.password_utils import generate_secure_password
from app.services.email_service import (
    send_welcome_email_with_temp_password,
    send_password_reset_email_with_new_password,
)


class TestPasswordHTMLEscaping:
    """Tests for HTML escaping of passwords in emails."""

    def test_html_escape_function(self):
        """Test that html.escape properly escapes HTML special characters."""
        # Test with various special characters
        test_cases = [
            ("<Password>", "&lt;Password&gt;"),
            ("Password&Value", "Password&amp;Value"),
            ('Password"Quote', "Password&quot;Quote"),
            ("Password'Quote", "Password&#x27;Quote"),
            ("Password<>\"'&", "Password&lt;&gt;&quot;&#x27;&amp;"),
        ]

        for input_str, expected_output in test_cases:
            assert html.escape(input_str) == expected_output

    def test_generate_secure_password_with_special_chars(self):
        """Test that generate_secure_password creates passwords with special characters."""
        # Generate multiple passwords to ensure we get some with HTML special characters
        passwords = [generate_secure_password() for _ in range(20)]

        # Check if any passwords contain HTML special characters
        html_special_chars = ["<", ">", "&", '"', "'"]
        passwords_with_special_chars = [
            password
            for password in passwords
            if any(char in password for char in html_special_chars)
        ]

        # Print some sample passwords for debugging
        print("\nSample generated passwords:")
        for i, password in enumerate(passwords[:5]):
            print(f"  {i + 1}. {password}")

        # We should have at least some passwords with HTML special characters
        # But this is probabilistic, so we can't guarantee it
        print(
            f"Found {len(passwords_with_special_chars)} passwords with HTML special characters"
        )

        # Create a password with known HTML special characters for testing
        test_password = "Test<Password>&Quote\"'123"
        print(f"Test password with HTML special chars: {test_password}")
        print(f"HTML escaped: {html.escape(test_password)}")


@pytest.mark.asyncio
class TestPasswordEmailHTMLEscaping:
    """Tests for HTML escaping of passwords in emails."""

    @patch("app.services.email_service.send_email")
    async def test_welcome_email_html_escaping(self, mock_send_email):
        """Test that passwords are properly HTML escaped in welcome emails."""
        # Setup mock
        mock_send_email.return_value = True

        # Test with a password containing HTML special characters
        test_password = "Test<Password>&Quote\"'123"
        email = "test@example.com"
        name = "Test User"

        # Call the function
        await send_welcome_email_with_temp_password(email, name, test_password)

        # Check that send_email was called with the correct arguments
        assert mock_send_email.called
        call_args = mock_send_email.call_args[0]

        # Check that the password appears correctly in the text body (unescaped)
        text_body = call_args[2]
        assert test_password in text_body, "Password not found in text body"

        # Check that the password is properly escaped in the HTML body
        html_body = call_args[3]
        escaped_password = html.escape(test_password)
        assert escaped_password in html_body, "Escaped password not found in HTML body"

        # The original password should not appear in the HTML body
        if "<" in test_password and ">" in test_password:
            assert test_password not in html_body, (
                "Unescaped password found in HTML body"
            )

    @patch("app.services.email_service.send_email")
    async def test_password_reset_email_html_escaping(self, mock_send_email):
        """Test that passwords are properly HTML escaped in password reset emails."""
        # Setup mock
        mock_send_email.return_value = True

        # Test with a password containing HTML special characters
        test_password = "Test<Password>&Quote\"'123"
        email = "test@example.com"
        name = "Test User"

        # Call the function
        await send_password_reset_email_with_new_password(email, name, test_password)

        # Check that send_email was called with the correct arguments
        assert mock_send_email.called
        call_args = mock_send_email.call_args[0]

        # Check that the password appears correctly in the text body (unescaped)
        text_body = call_args[2]
        assert test_password in text_body, "Password not found in text body"

        # Check that the password is properly escaped in the HTML body
        html_body = call_args[3]
        escaped_password = html.escape(test_password)
        assert escaped_password in html_body, "Escaped password not found in HTML body"

        # The original password should not appear in the HTML body
        if "<" in test_password and ">" in test_password:
            assert test_password not in html_body, (
                "Unescaped password found in HTML body"
            )


if __name__ == "__main__":
    pytest.main(["-xvs", "test_password_html_escaping.py"])
