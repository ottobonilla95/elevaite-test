import pytest
from datetime import datetime, timedelta, timezone

from app.db.models import User, MfaDeviceVerification
from app.core.security import get_password_hash, create_access_token

pytestmark = [pytest.mark.integration, pytest.mark.mfa, pytest.mark.admin]


class TestMfaAdminEndpoints:
    """Integration tests for MFA device management admin endpoints."""

    @pytest.fixture
    async def admin_user(self, test_session):
        """Create an admin user for testing."""
        admin_email = "admin@example.com"
        admin_password = "AdminPassword123!@#"
        hashed_password = get_password_hash(admin_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=admin_email,
            hashed_password=hashed_password,
            full_name="Admin User",
            status="active",
            is_verified=True,
            is_superuser=True,  # Make this user a superuser
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await test_session.execute(stmt)
        user_id = result.inserted_primary_key[0]
        await test_session.commit()

        return {
            "id": user_id,
            "email": admin_email,
            "password": admin_password,
        }

    @pytest.fixture
    async def regular_user(self, test_session):
        """Create a regular user for testing."""
        user_email = "user@example.com"
        user_password = "UserPassword123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Regular User",
            status="active",
            is_verified=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await test_session.execute(stmt)
        user_id = result.inserted_primary_key[0]
        await test_session.commit()

        return {
            "id": user_id,
            "email": user_email,
            "password": user_password,
        }

    @pytest.fixture
    def admin_headers(self, admin_user):
        """Create authorization headers for admin user."""
        # Create a JWT token for the admin user
        token_data = {
            "sub": str(admin_user["id"]),
            "email": admin_user["email"],
            "is_superuser": True,
        }
        access_token = create_access_token(token_data)

        return {
            "Authorization": f"Bearer {access_token}",
            "X-Tenant-ID": "default",
        }

    @pytest.fixture
    def user_headers(self, regular_user):
        """Create authorization headers for regular user."""
        token_data = {
            "sub": str(regular_user["id"]),
            "email": regular_user["email"],
            "is_superuser": False,
        }
        access_token = create_access_token(token_data)

        return {
            "Authorization": f"Bearer {access_token}",
            "X-Tenant-ID": "default",
        }

    @pytest.mark.asyncio
    async def test_admin_get_user_mfa_devices_success(
        self, test_client, test_session, admin_headers, regular_user
    ):
        """Test admin can view user's MFA devices."""
        # Create some MFA device verifications for the regular user
        verifications = [
            MfaDeviceVerification(
                user_id=regular_user["id"],
                device_fingerprint="device1_fingerprint",
                ip_address="192.168.1.100",
                user_agent="Chrome/91.0",
                verified_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                mfa_method="totp",
            ),
            MfaDeviceVerification(
                user_id=regular_user["id"],
                device_fingerprint="device2_fingerprint",
                ip_address="192.168.1.101",
                user_agent="Firefox/89.0",
                verified_at=datetime.now(timezone.utc) - timedelta(hours=1),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=23),
                mfa_method="sms",
            ),
        ]

        for verification in verifications:
            test_session.add(verification)
        await test_session.commit()

        # Admin requests user's MFA devices
        response = await test_client.get(
            f"/api/auth/admin/mfa-devices/{regular_user['id']}", headers=admin_headers
        )

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["user_id"] == regular_user["id"]
        assert len(response_data["device_verifications"]) == 2

        # Check first device
        device1 = response_data["device_verifications"][0]
        assert device1["device_fingerprint"].startswith("device")
        assert device1["device_fingerprint"].endswith("...")  # Should be truncated
        assert device1["ip_address"] in ["192.168.1.100", "192.168.1.101"]
        assert device1["mfa_method"] in ["totp", "sms"]

    @pytest.mark.asyncio
    async def test_admin_get_user_mfa_devices_no_devices(
        self, test_client, admin_headers, regular_user
    ):
        """Test admin viewing user with no MFA devices."""
        response = await test_client.get(
            f"/api/auth/admin/mfa-devices/{regular_user['id']}", headers=admin_headers
        )

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["user_id"] == regular_user["id"]
        assert len(response_data["device_verifications"]) == 0

    @pytest.mark.asyncio
    async def test_admin_get_user_mfa_devices_unauthorized(
        self, test_client, user_headers, regular_user
    ):
        """Test non-admin cannot view user's MFA devices."""
        response = await test_client.get(
            f"/api/auth/admin/mfa-devices/{regular_user['id']}", headers=user_headers
        )

        # Should be forbidden (403) or unauthorized (401)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_admin_revoke_user_mfa_devices_success(
        self, test_client, test_session, admin_headers, regular_user
    ):
        """Test admin can revoke user's MFA devices."""
        # Create some MFA device verifications for the regular user
        verifications = [
            MfaDeviceVerification(
                user_id=regular_user["id"],
                device_fingerprint="device1_fingerprint",
                ip_address="192.168.1.100",
                user_agent="Chrome/91.0",
                verified_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                mfa_method="totp",
            ),
            MfaDeviceVerification(
                user_id=regular_user["id"],
                device_fingerprint="device2_fingerprint",
                ip_address="192.168.1.101",
                user_agent="Firefox/89.0",
                verified_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                mfa_method="sms",
            ),
        ]

        for verification in verifications:
            test_session.add(verification)
        await test_session.commit()

        # Admin revokes user's MFA devices
        response = await test_client.post(
            f"/api/auth/admin/revoke-mfa-devices/{regular_user['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        assert "Revoked 2 MFA device verifications" in response_data["message"]

        # Verify devices were actually removed
        from sqlalchemy import select

        stmt = select(MfaDeviceVerification).where(
            MfaDeviceVerification.user_id == regular_user["id"]
        )
        result = await test_session.execute(stmt)
        remaining_verifications = result.scalars().all()

        assert len(remaining_verifications) == 0

    @pytest.mark.asyncio
    async def test_admin_revoke_user_mfa_devices_no_devices(
        self, test_client, admin_headers, regular_user
    ):
        """Test admin revoking MFA devices for user with no devices."""
        response = await test_client.post(
            f"/api/auth/admin/revoke-mfa-devices/{regular_user['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        assert "Revoked 0 MFA device verifications" in response_data["message"]

    @pytest.mark.asyncio
    async def test_admin_revoke_user_mfa_devices_unauthorized(
        self, test_client, user_headers, regular_user
    ):
        """Test non-admin cannot revoke user's MFA devices."""
        response = await test_client.post(
            f"/api/auth/admin/revoke-mfa-devices/{regular_user['id']}",
            headers=user_headers,
        )

        # Should be forbidden (403) or unauthorized (401)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_user_get_own_mfa_devices(
        self, test_client, test_session, user_headers, regular_user
    ):
        """Test user can view their own MFA devices."""
        # Create MFA device verification for the user
        verification = MfaDeviceVerification(
            user_id=regular_user["id"],
            device_fingerprint="user_device_fingerprint",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            verified_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            mfa_method="totp",
        )
        test_session.add(verification)
        await test_session.commit()

        response = await test_client.get(
            "/api/auth/me/mfa-devices", headers=user_headers
        )

        assert response.status_code == 200
        response_data = response.json()

        assert len(response_data["device_verifications"]) == 1
        device = response_data["device_verifications"][0]
        assert device["device_fingerprint"].startswith("user_device")
        assert device["device_fingerprint"].endswith("...")
        assert (
            device["platform"] == "Windows"
        )  # Should extract platform from user agent
        assert device["mfa_method"] == "totp"

    @pytest.mark.asyncio
    async def test_user_revoke_own_mfa_devices(
        self, test_client, test_session, user_headers, regular_user
    ):
        """Test user can revoke their own MFA devices."""
        # Create MFA device verifications for the user
        verifications = [
            MfaDeviceVerification(
                user_id=regular_user["id"],
                device_fingerprint="device1_fingerprint",
                ip_address="192.168.1.100",
                user_agent="Chrome/91.0",
                verified_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                mfa_method="totp",
            ),
            MfaDeviceVerification(
                user_id=regular_user["id"],
                device_fingerprint="device2_fingerprint",
                ip_address="192.168.1.101",
                user_agent="Firefox/89.0",
                verified_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                mfa_method="sms",
            ),
        ]

        for verification in verifications:
            test_session.add(verification)
        await test_session.commit()

        response = await test_client.post(
            "/api/auth/me/revoke-mfa-devices", headers=user_headers
        )

        assert response.status_code == 200
        response_data = response.json()

        assert "Revoked 2 MFA device verifications" in response_data["message"]

        # Verify devices were actually removed
        from sqlalchemy import select

        stmt = select(MfaDeviceVerification).where(
            MfaDeviceVerification.user_id == regular_user["id"]
        )
        result = await test_session.execute(stmt)
        remaining_verifications = result.scalars().all()

        assert len(remaining_verifications) == 0

    @pytest.mark.asyncio
    async def test_user_get_mfa_devices_unauthorized(self, test_client):
        """Test unauthorized access to MFA devices endpoint."""
        response = await test_client.get(
            "/api/auth/me/mfa-devices",
            headers={"X-Tenant-ID": "default"},  # No authorization header
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_user_revoke_mfa_devices_unauthorized(self, test_client):
        """Test unauthorized access to revoke MFA devices endpoint."""
        response = await test_client.post(
            "/api/auth/me/revoke-mfa-devices",
            headers={"X-Tenant-ID": "default"},  # No authorization header
        )

        assert response.status_code == 401
