"""Tests for the activity_log module."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from app.db.activity_log import log_user_activity
from app.db.models import UserActivity


@pytest.mark.asyncio
class TestActivityLog:
    """Tests for the activity_log module."""

    async def test_log_user_activity(self):
        """Test the log_user_activity function."""
        # Create a mock session
        mock_session = AsyncMock()
        mock_session.run_sync = AsyncMock()

        # Call the function
        await log_user_activity(
            session=mock_session,
            user_id=1,
            action="login",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            details={"source": "web"},
        )

        # Check that session.run_sync was called with a function
        assert mock_session.run_sync.called
        # Get the lambda function that was passed to run_sync
        add_func = mock_session.run_sync.call_args[0][0]

        # Create a mock SQLAlchemy session to pass to the lambda
        mock_sync_session = AsyncMock()
        # Call the lambda with our mock
        add_func(mock_sync_session)

        # Check that add was called on the sync session
        assert mock_sync_session.add.called
        activity = mock_sync_session.add.call_args[0][0]
        assert isinstance(activity, UserActivity)
        assert activity.user_id == 1
        assert activity.action == "login"
        assert activity.ip_address == "127.0.0.1"
        assert activity.user_agent == "Mozilla/5.0"
        assert activity.details == {"source": "web"}

        # Check that session.commit was called
        assert mock_session.commit.called

    async def test_log_user_activity_minimal(self):
        """Test log_user_activity with minimal parameters."""
        # Create a mock session
        mock_session = AsyncMock()
        mock_session.run_sync = AsyncMock()

        # Call the function with only required parameters
        await log_user_activity(session=mock_session, user_id=1, action="logout")

        # Check that session.run_sync was called with a function
        assert mock_session.run_sync.called
        # Get the lambda function that was passed to run_sync
        add_func = mock_session.run_sync.call_args[0][0]

        # Create a mock SQLAlchemy session to pass to the lambda
        mock_sync_session = AsyncMock()
        # Call the lambda with our mock
        add_func(mock_sync_session)

        # Check that add was called on the sync session
        assert mock_sync_session.add.called
        activity = mock_sync_session.add.call_args[0][0]
        assert isinstance(activity, UserActivity)
        assert activity.user_id == 1
        assert activity.action == "logout"
        assert activity.ip_address is None
        assert activity.user_agent is None
        assert activity.details is None

        # Check that session.commit was called
        assert mock_session.commit.called

    @patch("app.db.activity_log.datetime")
    async def test_log_user_activity_timestamp(self, mock_datetime):
        """Test that timestamp is set correctly."""
        # Setup mock datetime
        mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.run_sync = AsyncMock()

        # Call the function
        await log_user_activity(session=mock_session, user_id=1, action="login")

        # Check that session.run_sync was called with a function
        assert mock_session.run_sync.called
        # Get the lambda function that was passed to run_sync
        add_func = mock_session.run_sync.call_args[0][0]

        # Create a mock SQLAlchemy session to pass to the lambda
        mock_sync_session = AsyncMock()
        # Call the lambda with our mock
        add_func(mock_sync_session)

        # Check that timestamp was set to the mocked datetime
        activity = mock_sync_session.add.call_args[0][0]
        assert activity.timestamp == mock_now
