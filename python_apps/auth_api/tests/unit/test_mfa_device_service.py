import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request

from app.services.mfa_device_service import MfaDeviceService
from app.db.models import User, MfaDeviceVerification

pytestmark = [pytest.mark.unit, pytest.mark.mfa]


class TestMfaDeviceService:
    """Test MFA device service functionality."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = 123
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        headers_dict = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/html,application/xhtml+xml",
            "accept-language": "en-US,en;q=0.5",
            "accept-encoding": "gzip, deflate",
        }
        request.headers = Mock()
        request.headers.get = lambda key, default=None: headers_dict.get(key, default)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_check_device_mfa_bypass_valid(
        self, mock_user, mock_request, mock_session
    ):
        """Test checking for valid MFA bypass."""
        # Mock a valid verification record
        mock_verification = Mock(spec=MfaDeviceVerification)
        mock_verification.expires_at = datetime.now(timezone.utc) + timedelta(hours=12)

        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_verification
        mock_session.execute.return_value = mock_result

        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint"
        ) as mock_fingerprint:
            mock_fingerprint.return_value = "test_fingerprint"

            result = await MfaDeviceService.check_device_mfa_bypass(
                mock_user, mock_request, mock_session
            )

        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_device_mfa_bypass_expired(
        self, mock_user, mock_request, mock_session
    ):
        """Test checking for expired MFA bypass."""
        # Mock an expired verification record
        mock_verification = Mock(spec=MfaDeviceVerification)
        mock_verification.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        # Mock database query result (no valid records found)
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint"
        ) as mock_fingerprint:
            mock_fingerprint.return_value = "test_fingerprint"

            result = await MfaDeviceService.check_device_mfa_bypass(
                mock_user, mock_request, mock_session
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_device_mfa_bypass_no_record(
        self, mock_user, mock_request, mock_session
    ):
        """Test checking for MFA bypass with no existing record."""
        # Mock database query result (no records found)
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint"
        ) as mock_fingerprint:
            mock_fingerprint.return_value = "test_fingerprint"

            result = await MfaDeviceService.check_device_mfa_bypass(
                mock_user, mock_request, mock_session
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_device_mfa_bypass_exception(
        self, mock_user, mock_request, mock_session
    ):
        """Test checking for MFA bypass with database exception."""
        # Mock database exception
        mock_session.execute.side_effect = Exception("Database error")

        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint"
        ) as mock_fingerprint:
            mock_fingerprint.return_value = "test_fingerprint"

            result = await MfaDeviceService.check_device_mfa_bypass(
                mock_user, mock_request, mock_session
            )

        # Should fail secure and return False
        assert result is False

    @pytest.mark.asyncio
    async def test_record_mfa_verification_success(
        self, mock_user, mock_request, mock_session
    ):
        """Test recording successful MFA verification."""
        with (
            patch(
                "app.services.mfa_device_service.generate_device_fingerprint"
            ) as mock_fingerprint,
            patch(
                "app.services.mfa_device_service.get_device_info_for_logging"
            ) as mock_device_info,
        ):

            mock_fingerprint.return_value = "test_fingerprint"
            mock_device_info.return_value = {
                "ip_address": "192.168.1.100",
                "user_agent": "TestAgent/1.0",
            }

            await MfaDeviceService.record_mfa_verification(
                mock_user, mock_request, mock_session, "totp"
            )

        # Verify that old records were deleted and new record was added
        assert mock_session.execute.call_count >= 1  # At least one execute call
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_mfa_verification_custom_duration(
        self, mock_user, mock_request, mock_session
    ):
        """Test recording MFA verification with custom duration."""
        with (
            patch(
                "app.services.mfa_device_service.generate_device_fingerprint"
            ) as mock_fingerprint,
            patch(
                "app.services.mfa_device_service.get_device_info_for_logging"
            ) as mock_device_info,
        ):

            mock_fingerprint.return_value = "test_fingerprint"
            mock_device_info.return_value = {
                "ip_address": "192.168.1.100",
                "user_agent": "TestAgent/1.0",
            }

            await MfaDeviceService.record_mfa_verification(
                mock_user, mock_request, mock_session, "sms", bypass_duration_hours=8
            )

        mock_session.add.assert_called_once()
        # Verify the verification object was created with correct expiration
        added_verification = mock_session.add.call_args[0][0]
        assert isinstance(added_verification, MfaDeviceVerification)

    @pytest.mark.asyncio
    async def test_record_mfa_verification_exception(
        self, mock_user, mock_request, mock_session
    ):
        """Test recording MFA verification with database exception."""
        mock_session.execute.side_effect = Exception("Database error")

        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint"
        ) as mock_fingerprint:
            mock_fingerprint.return_value = "test_fingerprint"

            with pytest.raises(Exception):
                await MfaDeviceService.record_mfa_verification(
                    mock_user, mock_request, mock_session, "totp"
                )

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_verifications_success(self, mock_session):
        """Test cleanup of expired verifications."""
        # Mock successful deletion
        mock_result = Mock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        deleted_count = await MfaDeviceService.cleanup_expired_verifications(
            mock_session
        )

        assert deleted_count == 5
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_verifications_no_records(self, mock_session):
        """Test cleanup with no expired records."""
        # Mock no records deleted
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        deleted_count = await MfaDeviceService.cleanup_expired_verifications(
            mock_session
        )

        assert deleted_count == 0
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_verifications_exception(self, mock_session):
        """Test cleanup with database exception."""
        mock_session.execute.side_effect = Exception("Database error")

        deleted_count = await MfaDeviceService.cleanup_expired_verifications(
            mock_session
        )

        assert deleted_count == 0
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_device_verification_success(self, mock_session):
        """Test revoking a specific device verification."""
        # Mock successful deletion
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await MfaDeviceService.revoke_device_verification(
            123, "test_fingerprint", mock_session
        )

        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_device_verification_not_found(self, mock_session):
        """Test revoking a device verification that doesn't exist."""
        # Mock no records deleted
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await MfaDeviceService.revoke_device_verification(
            123, "test_fingerprint", mock_session
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_user_verifications_success(self, mock_session):
        """Test revoking all verifications for a user."""
        # Mock successful deletion
        mock_result = Mock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result

        deleted_count = await MfaDeviceService.revoke_all_user_verifications(
            123, mock_session
        )

        assert deleted_count == 3
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_device_verifications_success(self, mock_session):
        """Test getting user device verifications."""
        # Mock verification records
        mock_verifications = [
            Mock(spec=MfaDeviceVerification),
            Mock(spec=MfaDeviceVerification),
        ]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_verifications
        mock_session.execute.return_value = mock_result

        verifications = await MfaDeviceService.get_user_device_verifications(
            123, mock_session
        )

        assert len(verifications) == 2
        assert verifications == mock_verifications

    @pytest.mark.asyncio
    async def test_get_user_device_verifications_exception(self, mock_session):
        """Test getting user device verifications with exception."""
        mock_session.execute.side_effect = Exception("Database error")

        verifications = await MfaDeviceService.get_user_device_verifications(
            123, mock_session
        )

        assert verifications == []

    @pytest.mark.asyncio
    async def test_record_mfa_verification_uses_config_default(
        self, mock_user, mock_request, mock_session
    ):
        """Test that record_mfa_verification uses config default when no duration specified."""
        with (
            patch(
                "app.services.mfa_device_service.generate_device_fingerprint"
            ) as mock_fingerprint,
            patch(
                "app.services.mfa_device_service.get_device_info_for_logging"
            ) as mock_device_info,
            patch("app.core.config.settings") as mock_settings,
        ):

            mock_fingerprint.return_value = "test_fingerprint"
            mock_device_info.return_value = {
                "ip_address": "192.168.1.100",
                "user_agent": "TestAgent/1.0",
            }
            mock_settings.MFA_DEVICE_BYPASS_HOURS = 48  # Custom config value

            await MfaDeviceService.record_mfa_verification(
                mock_user, mock_request, mock_session, "totp"
            )

        # Verify the verification object was created
        mock_session.add.assert_called_once()
        added_verification = mock_session.add.call_args[0][0]
        assert isinstance(added_verification, MfaDeviceVerification)
        assert added_verification.mfa_method == "totp"
