import pytest
import re
from unittest.mock import patch, MagicMock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.password_utils import generate_secure_password
from app.services.email_service import (
    send_email,
    send_password_reset_email_with_new_password,
)


class TestOTPGeneration:

    def test_generate_multiple_passwords(self):
        """Generate multiple passwords and analyze them for potential problematic characters."""
        # Generate a large sample of passwords
        num_samples = 100
        passwords = [generate_secure_password() for _ in range(num_samples)]

        # Check for patterns or problematic characters
        problematic_chars = []
        special_chars_count = {}
        html_problematic_count = 0
        email_problematic_count = 0

        # Print some sample passwords
        print("\nSample generated passwords:")
        for i in range(min(10, num_samples)):
            print(f"  {i+1}. {passwords[i]}")

        for password in passwords:
            # Count special characters
            for char in password:
                if not char.isalnum():
                    if char not in special_chars_count:
                        special_chars_count[char] = 0
                    special_chars_count[char] += 1

                    # Check if this character might be problematic in HTML contexts
                    if char in "<>&\"'":
                        if char not in problematic_chars:
                            problematic_chars.append(char)
                        html_problematic_count += 1

                    # Check for characters that might be problematic in emails
                    if char in "\\^{}|~[]:;,":
                        email_problematic_count += 1

        # Print statistics
        print(f"\nGenerated {num_samples} passwords")
        print(f"Special characters distribution: {special_chars_count}")

        if problematic_chars:
            print(f"Potentially problematic HTML characters found: {problematic_chars}")
            print(
                f"Number of passwords with HTML-problematic characters: {html_problematic_count}"
            )

        print(
            f"Number of passwords with email-problematic characters: {email_problematic_count}"
        )

        # Check for specific patterns that might cause issues
        print("\nAnalyzing for specific problematic patterns:")

        # Check for consecutive special characters
        consecutive_special = 0
        for password in passwords:
            prev_special = False
            for char in password:
                is_special = not char.isalnum()
                if is_special and prev_special:
                    consecutive_special += 1
                    break
                prev_special = is_special

        print(f"Passwords with consecutive special characters: {consecutive_special}")

        # Ensure all passwords meet the requirements
        for password in passwords:
            assert len(password) == 16
            assert any(c.islower() for c in password)
            assert any(c.isupper() for c in password)
            assert any(c.isdigit() for c in password)
            # Accept any non-alphanumeric as a special character
            assert any(not c.isalnum() for c in password)


@pytest.mark.asyncio
class TestOTPEmailRendering:
    """Tests for how OTPs are rendered in emails."""

    @patch("app.services.email_service.smtplib.SMTP")
    async def test_password_in_email(self, mock_smtp):
        """Test that passwords are properly included in emails without being broken."""
        # Setup mock SMTP
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        # Generate a set of passwords with various special characters
        passwords = [
            generate_secure_password(),
            # Add some passwords with known problematic patterns
            "Test<Password>123!",
            "Pass&word\"Quote'123",
            "P@ssw0rd+With=Chars",
            "EndsWith!@#$%^&*()_+",
        ]

        for password in passwords:
            # Send an email with this password
            result = await send_email(
                recipient="test@example.com",
                subject="Test Password Email",
                text_body=f"Your password is: {password}",
                html_body=f"<p>Your password is: <strong>{password}</strong></p>",
            )

            # Verify the email was sent
            assert result is True

            # Capture the email content
            call_args = mock_smtp_instance.sendmail.call_args
            email_content = call_args[0][2]  # The third argument is the email content

            # Check if the password appears correctly in the email
            # For text part
            assert (
                password in email_content
            ), f"Password '{password}' not found in email content"

            # For HTML part (this is more complex as it might be encoded)
            # Extract the HTML part
            html_match = re.search(
                r"Content-Type: text/html.*?<strong>(.*?)</strong>",
                email_content,
                re.DOTALL,
            )
            if html_match:
                html_password = html_match.group(1)
                from html import escape as _escape

                assert (
                    password in html_password or _escape(password) in html_password
                ), f"Password '{password}' not correctly rendered in HTML"

    @patch("app.services.email_service.send_email")
    async def test_password_reset_email_content(self, mock_send_email):
        """Test that the password reset email properly includes the password."""
        # Setup mock
        mock_send_email.return_value = True

        # Generate passwords with potential problematic characters
        passwords = [
            generate_secure_password(),
            "Test<Password>123!",
            "Pass&word\"Quote'123",
            "P@ssw0rd+With=Chars",
            "EndsWith!@#$%^&*()_+",
            "Brackets{[]}|^~",
            "Comma,Semicolon;Colon:",
        ]

        print("\nTesting email rendering with problematic passwords:")
        for password in passwords:
            print(f"Testing password: {password}")

            # Call the function
            email = "test@example.com"
            name = "Test User"
            result = await send_password_reset_email_with_new_password(
                email, name, password
            )

            # Check that send_email was called with the correct arguments
            assert mock_send_email.called
            call_args = mock_send_email.call_args[0]

            # Check that the password appears correctly in both text and HTML bodies
            text_body = call_args[2]
            html_body = call_args[3]

            # Check text body
            assert (
                password in text_body
            ), f"Password '{password}' not found in text body"

            # For HTML body, we need to check if the password is properly escaped
            # Extract the password from the HTML
            import re
            from html import escape

            # The password should be in a styled paragraph
            html_match = re.search(
                r'<p style="[^"]*">\s*(.*?)\s*</p>', html_body, re.DOTALL
            )
            if html_match:
                html_password_section = html_match.group(1)
                print(f"  HTML rendering: {html_password_section}")

                # Check if the password is properly included
                # If the password contains HTML special chars, it should be escaped
                if any(c in '<>&"' for c in password):
                    escaped_password = escape(password)
                    assert (
                        escaped_password in html_password_section
                        or password in html_password_section
                    ), f"Password '{password}' not properly escaped in HTML"
                else:
                    assert (
                        password in html_password_section
                    ), f"Password '{password}' not found in HTML section"
            else:
                # If we can't find the styled paragraph, just check if the password is in the HTML
                from html import escape as _escape

                assert (
                    password in html_body or _escape(password) in html_body
                ), f"Password '{password}' not found in HTML body"

            # Reset the mock for the next iteration
            mock_send_email.reset_mock()


if __name__ == "__main__":
    pytest.main(["-xvs", "test_otp_sanitation.py"])
