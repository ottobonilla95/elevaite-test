"""Unit tests for the User model."""

from datetime import datetime, timezone

from app.db.models import User


class TestUserModel:
    """Tests for the User model."""

    def test_user_creation(self):
        """Test creating a User model instance."""
        # Create a user
        user = User(email="test@example.com", hashed_password="hashed_password", full_name="Test User")

        # Verify the user attributes
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password"
        assert user.full_name == "Test User"

    def test_user_repr(self):
        """Test the User model's string representation."""
        user = User(id=1, email="test@example.com", hashed_password="hashed_password", full_name="Test User")

        # Verify the string representation
        assert str(user) == "<User test@example.com>"

    def test_user_properties(self):
        """Test the User model's properties."""
        # Create a user with a creation timestamp
        now = datetime.now(timezone.utc)
        user = User(email="test@example.com", hashed_password="hashed_password", full_name="Test User", created_at=now)

        # Verify the properties
        assert user.created_at == now
