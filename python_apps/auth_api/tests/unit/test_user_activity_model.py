"""Tests for the UserActivity model."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.db.models import UserActivity, User


class TestUserActivityModel:
    """Tests for the UserActivity model."""

    def test_user_activity_creation(self):
        """Test creating a UserActivity instance."""
        # Create a mock user
        user = MagicMock(spec=User)
        user.id = 1

        # Create a UserActivity instance
        activity = UserActivity(
            user_id=user.id,
            action="login",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(timezone.utc),
            details={"source": "web"},
        )

        # Check attributes
        assert activity.user_id == 1
        assert activity.action == "login"
        assert activity.ip_address == "127.0.0.1"
        assert activity.user_agent == "Mozilla/5.0"
        assert isinstance(activity.timestamp, datetime)
        assert activity.details == {"source": "web"}

    def test_user_activity_repr(self):
        """Test the string representation of UserActivity."""
        activity = UserActivity(id=42, user_id=1, action="password_reset")

        # Check __repr__ method
        assert str(activity) == "<UserActivity 42 - password_reset by User 1>"

    def test_user_activity_defaults(self):
        """Test default values for UserActivity."""
        # Create with minimal required fields
        activity = UserActivity(
            user_id=1,
            action="login",
            timestamp=datetime.now(
                timezone.utc
            ),  # We need to set this manually in tests
        )

        # Check default values
        assert activity.ip_address is None
        assert activity.user_agent is None
        assert activity.details is None
        assert isinstance(activity.timestamp, datetime)
        assert activity.timestamp.tzinfo is not None  # Should be timezone-aware
