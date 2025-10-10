from app.core.password_utils import generate_secure_password, is_password_temporary


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

        # Check that it contains at least one special character (non-alphanumeric)
        assert any(not c.isalnum() for c in password)

        # Generate a password with custom length
        custom_length = 24
        password = generate_secure_password(custom_length)
        assert len(password) == custom_length

    def test_is_password_temporary(self):
        """Test that is_password_temporary correctly identifies test credentials."""
        # Test with known accounts should not be treated as temporary by default
        is_test, message = is_password_temporary(
            "panagiotis.v@iopex.com", "password123"
        )
        assert is_test is False
        assert message == ""

        # Test with regular credentials
        is_test, message = is_password_temporary(
            "regular@example.com", "regularpassword"
        )
        assert is_test is False
        assert message == ""
