import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.tasks.cleanup_tasks import (
    cleanup_expired_mfa_verifications,
    start_cleanup_tasks,
)

pytestmark = [pytest.mark.unit, pytest.mark.mfa, pytest.mark.cleanup]


class TestCleanupTasks:
    """Test cleanup task functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_mfa_verifications_success(self):
        """Test successful cleanup of expired MFA verifications."""
        with (
            patch("app.tasks.cleanup_tasks.get_async_session") as mock_get_session,
            patch("app.tasks.cleanup_tasks.mfa_device_service") as mock_service,
        ):
            # Mock async session generator
            mock_session = AsyncMock()

            async def _gen():
                yield mock_session

            mock_get_session.return_value = _gen()

            # Mock service method
            mock_service.cleanup_expired_verifications.return_value = 5

            await cleanup_expired_mfa_verifications()

            # Verify service was called with session
            mock_service.cleanup_expired_verifications.assert_called_once_with(
                mock_session
            )

    @pytest.mark.asyncio
    async def test_cleanup_expired_mfa_verifications_exception(self):
        """Test cleanup with exception handling."""
        with (
            patch("app.tasks.cleanup_tasks.get_async_session") as mock_get_session,
            patch("app.tasks.cleanup_tasks.mfa_device_service") as mock_service,
            patch("app.tasks.cleanup_tasks.logger") as mock_logger,
        ):
            # Mock async session generator
            mock_session = AsyncMock()

            async def _gen():
                yield mock_session

            mock_get_session.return_value = _gen()

            # Mock service method to raise exception
            mock_service.cleanup_expired_verifications.side_effect = Exception(
                "Database error"
            )

            await cleanup_expired_mfa_verifications()

            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert (
                "Error during MFA verification cleanup"
                in mock_logger.error.call_args[0][0]
            )

    @pytest.mark.asyncio
    async def test_start_mfa_cleanup_task_runs_periodically(self):
        """Test that cleanup task runs periodically."""
        call_count = 0

        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:  # Stop after 3 iterations
                raise asyncio.CancelledError()

        with (
            patch(
                "app.tasks.cleanup_tasks.cleanup_expired_mfa_verifications"
            ) as mock_cleanup,
            patch("asyncio.sleep", side_effect=mock_sleep) as mock_sleep_patch,
            patch("app.tasks.cleanup_tasks.logger"),
        ):
            # Run the task until our sleep side-effect cancels internally
            await start_cleanup_tasks()

            # Verify cleanup was called multiple times
            assert mock_cleanup.call_count >= 2

            # Verify sleep was called with correct duration (3600 seconds = 1 hour)
            mock_sleep_patch.assert_called_with(3600)

    @pytest.mark.asyncio
    async def test_start_mfa_cleanup_task_handles_exceptions(self):
        """Test that cleanup task handles exceptions and continues running."""
        call_count = 0

        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:  # Stop after 3 iterations
                raise asyncio.CancelledError()

        async def mock_cleanup():
            nonlocal call_count
            if call_count == 1:
                raise Exception("First cleanup failed")
            # Second cleanup succeeds

        with (
            patch(
                "app.tasks.cleanup_tasks.cleanup_expired_mfa_verifications",
                side_effect=mock_cleanup,
            ) as mock_cleanup_patch,
            patch("asyncio.sleep", side_effect=mock_sleep) as mock_sleep_patch,
            patch("app.tasks.cleanup_tasks.logger") as mock_logger,
        ):
            # Run the task until our sleep side-effect cancels internally
            await start_cleanup_tasks()

            # Verify cleanup was attempted at least once (loop continues after error)
            assert mock_cleanup_patch.call_count >= 1

            # Verify error was logged
            mock_logger.error.assert_called()
            assert (
                "Unexpected error in cleanup tasks" in mock_logger.error.call_args[0][0]
            )

            # Verify task continued running (sleep called with 60 seconds after error)
            assert any(call[0][0] == 60 for call in mock_sleep_patch.call_args_list)

    @pytest.mark.asyncio
    async def test_start_mfa_cleanup_task_cancellation(self):
        """Test that cleanup task handles cancellation gracefully."""
        with (
            patch("app.tasks.cleanup_tasks.cleanup_expired_mfa_verifications"),
            patch("asyncio.sleep", side_effect=asyncio.CancelledError()),
            patch("app.tasks.cleanup_tasks.logger") as mock_logger,
        ):
            # Run the task and expect cancellation to be swallowed by the loop
            await start_cleanup_tasks()

            # Verify cancellation was logged with current message
            mock_logger.info.assert_called_with("Cleanup tasks cancelled")

    @pytest.mark.asyncio
    async def test_cleanup_task_integration_with_real_timing(self):
        """Test cleanup task with real timing (but very short intervals)."""
        cleanup_calls = []

        async def mock_cleanup():
            cleanup_calls.append(datetime.now())

        # Use very short sleep intervals for testing
        original_sleep = asyncio.sleep

        async def fast_sleep(duration):
            # Sleep for much shorter time in tests
            if duration == 3600:  # Main loop sleep
                await original_sleep(0.1)  # 100ms instead of 1 hour
            elif duration == 60:  # Error recovery sleep
                await original_sleep(0.05)  # 50ms instead of 1 minute
            else:
                await original_sleep(duration)

        with (
            patch(
                "app.tasks.cleanup_tasks.cleanup_expired_mfa_verifications",
                side_effect=mock_cleanup,
            ),
            patch("asyncio.sleep", side_effect=fast_sleep),
            patch("app.tasks.cleanup_tasks.logger"),
        ):
            # Run the task for a short time
            task = asyncio.create_task(start_cleanup_tasks())

            # Let it run for a bit
            await asyncio.sleep(0.3)  # 300ms

            # Cancel the task
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify cleanup was called multiple times
            assert len(cleanup_calls) >= 2

            # Verify calls were spaced out
            if len(cleanup_calls) >= 2:
                time_diff = cleanup_calls[1] - cleanup_calls[0]
                assert time_diff.total_seconds() >= 0.08  # At least 80ms apart

    @pytest.mark.asyncio
    async def test_cleanup_with_session_context_manager_error(self):
        """Test cleanup when session context manager fails."""
        with (
            patch("app.tasks.cleanup_tasks.get_async_session") as mock_get_session,
            patch("app.tasks.cleanup_tasks.logger") as mock_logger,
        ):
            # Mock async session generator to raise during iteration
            async def _gen():
                raise Exception("Session creation failed")
                yield  # unreachable, keeps it an async generator

            mock_get_session.return_value = _gen()

            await cleanup_expired_mfa_verifications()

            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert (
                "Error during MFA verification cleanup"
                in mock_logger.error.call_args[0][0]
            )

    def test_cleanup_task_module_imports(self):
        """Test that all required modules can be imported."""
        # This test ensures all imports work correctly
        from app.tasks.cleanup_tasks import (
            cleanup_expired_mfa_verifications,
            start_cleanup_tasks,
        )

        # Verify functions are callable
        assert callable(cleanup_expired_mfa_verifications)
        assert callable(start_cleanup_tasks)

    @pytest.mark.asyncio
    async def test_cleanup_task_logging_levels(self):
        """Test that cleanup task uses appropriate logging levels."""
        with (
            patch("app.tasks.cleanup_tasks.get_async_session") as mock_get_session,
            patch("app.tasks.cleanup_tasks.mfa_device_service") as mock_service,
            patch("app.tasks.cleanup_tasks.logger") as mock_logger,
        ):
            # Mock async session generator
            mock_session = AsyncMock()

            async def _gen():
                yield mock_session

            mock_get_session.return_value = _gen()

            # Test with successful cleanup that removes records
            mock_service.cleanup_expired_verifications = AsyncMock(return_value=5)
            await cleanup_expired_mfa_verifications()

            # Should log info when records are cleaned up
            mock_logger.info.assert_called_once()
            assert (
                "Cleaned up 5 expired MFA device verifications"
                in mock_logger.info.call_args[0][0]
            )

            # Reset mock
            mock_logger.reset_mock()

            # Test with no records to clean up
            mock_service.cleanup_expired_verifications = AsyncMock(return_value=0)
            await cleanup_expired_mfa_verifications()

            # Should not log info when no records are cleaned up
            mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_cleanup_task_initial_logging(self):
        """Test that cleanup task logs startup message."""
        with (
            patch("app.tasks.cleanup_tasks.cleanup_expired_mfa_verifications"),
            patch("asyncio.sleep", side_effect=asyncio.CancelledError()),
            patch("app.tasks.cleanup_tasks.logger") as mock_logger,
        ):
            # Run the task and expect immediate cancellation to be swallowed
            await start_cleanup_tasks()

            # Verify startup message was logged (updated message)
            mock_logger.info.assert_any_call(
                "Starting cleanup tasks (sessions and MFA verifications)"
            )

    @pytest.mark.asyncio
    async def test_cleanup_debug_logging(self):
        """Test debug logging during cleanup cycles."""
        call_count = 0

        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Stop after 2 iterations
                raise asyncio.CancelledError()

        with (
            patch("app.tasks.cleanup_tasks.cleanup_expired_mfa_verifications"),
            patch("asyncio.sleep", side_effect=mock_sleep),
            patch("app.tasks.cleanup_tasks.logger") as mock_logger,
        ):
            # Run the task until it's cancelled internally
            await start_cleanup_tasks()

            # Verify debug message was logged with current message
            mock_logger.debug.assert_called_with("Running scheduled cleanup tasks")
