import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.db.models import User, MfaDeviceVerification
from app.core.security import get_password_hash

pytestmark = [pytest.mark.integration, pytest.mark.mfa]


class TestMfaDeviceBypassIntegration:
    """Integration tests for MFA device bypass."""

    @pytest.mark.asyncio
    async def test_login_without_mfa_bypass_requires_mfa(
        self, test_client, test_session
    ):
        """Test that login without MFA bypass requires MFA when enabled."""
        # Create a user with TOTP MFA enabled
        user_email = "mfa_test@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        # Insert user with MFA enabled
        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="MFA Test User",
            status="active",
            is_verified=True,
            mfa_enabled=True,
            mfa_secret="JBSWY3DPEHPK3PXP",  # Test TOTP secret
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        # Attempt login without TOTP code
        login_data = {
            "email": user_email,
            "password": user_password,
        }

        response = await test_client.post(
            "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
        )

        # Should require MFA
        assert response.status_code == 400
        response_data = response.json()
        assert "TOTP code required" in response_data["detail"]

    @pytest.mark.asyncio
    async def test_login_with_valid_mfa_creates_bypass(self, test_client, test_session):
        """Test that successful MFA login creates a device bypass."""
        # Create a user with TOTP MFA enabled
        user_email = "mfa_bypass_test@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="MFA Bypass Test User",
            status="active",
            is_verified=True,
            mfa_enabled=True,
            mfa_secret="JBSWY3DPEHPK3PXP",  # Test TOTP secret
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await test_session.execute(stmt)
        await test_session.commit()

        # Mock TOTP verification to always succeed
        with patch("app.services.auth_orm.verify_totp", return_value=True):
            login_data = {
                "email": user_email,
                "password": user_password,
                "totp_code": "123456",  # Mock code
            }

            response = await test_client.post(
                "/api/auth/login",
                json=login_data,
                headers={
                    "X-Tenant-ID": "default",
                    "User-Agent": "TestBrowser/1.0",
                },
            )

        # Should succeed
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data

        # Verify that a device verification was created
        from sqlalchemy import select

        stmt = select(MfaDeviceVerification).where(
            MfaDeviceVerification.user_id == result.inserted_primary_key[0]
        )
        result = await test_session.execute(stmt)
        verification = result.scalars().first()

        assert verification is not None
        assert verification.mfa_method == "totp"
        assert verification.expires_at > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_subsequent_login_uses_bypass(self, test_client, test_session):
        """Test that subsequent login from same device uses bypass."""
        # Create a user with TOTP MFA enabled
        user_email = "bypass_subsequent@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Bypass Subsequent Test User",
            status="active",
            is_verified=True,
            mfa_enabled=True,
            mfa_secret="JBSWY3DPEHPK3PXP",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await test_session.execute(stmt)
        user_id = result.inserted_primary_key[0]
        await test_session.commit()

        # Create a device verification manually
        device_verification = MfaDeviceVerification(
            user_id=user_id,
            device_fingerprint="test_device_fingerprint",
            ip_address="127.0.0.1",
            user_agent="TestBrowser/1.0",
            verified_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            mfa_method="totp",
        )
        test_session.add(device_verification)
        await test_session.commit()

        # Mock device fingerprint generation to return our test fingerprint
        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint",
            return_value="test_device_fingerprint",
        ):

            login_data = {
                "email": user_email,
                "password": user_password,
                # No TOTP code provided
            }

            response = await test_client.post(
                "/api/auth/login",
                json=login_data,
                headers={
                    "X-Tenant-ID": "default",
                    "User-Agent": "TestBrowser/1.0",
                },
            )

        # Should succeed without MFA
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data

    @pytest.mark.asyncio
    async def test_expired_bypass_requires_mfa_again(self, test_client, test_session):
        """Test that expired bypass requires MFA again."""
        # Create a user with TOTP MFA enabled
        user_email = "expired_bypass@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Expired Bypass Test User",
            status="active",
            is_verified=True,
            mfa_enabled=True,
            mfa_secret="JBSWY3DPEHPK3PXP",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await test_session.execute(stmt)
        user_id = result.inserted_primary_key[0]
        await test_session.commit()

        # Create an expired device verification
        device_verification = MfaDeviceVerification(
            user_id=user_id,
            device_fingerprint="expired_device_fingerprint",
            ip_address="127.0.0.1",
            user_agent="TestBrowser/1.0",
            verified_at=datetime.now(timezone.utc) - timedelta(hours=25),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            mfa_method="totp",
        )
        test_session.add(device_verification)
        await test_session.commit()

        # Mock device fingerprint generation
        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint",
            return_value="expired_device_fingerprint",
        ):

            login_data = {
                "email": user_email,
                "password": user_password,
                # No TOTP code provided
            }

            response = await test_client.post(
                "/api/auth/login",
                json=login_data,
                headers={
                    "X-Tenant-ID": "default",
                    "User-Agent": "TestBrowser/1.0",
                },
            )

        # Should require MFA again
        assert response.status_code == 400
        response_data = response.json()
        assert "TOTP code required" in response_data["detail"]

    @pytest.mark.asyncio
    async def test_different_device_requires_mfa(self, test_client, test_session):
        """Test that different device requires MFA even with existing bypass."""
        # Create a user with TOTP MFA enabled
        user_email = "different_device@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Different Device Test User",
            status="active",
            is_verified=True,
            mfa_enabled=True,
            mfa_secret="JBSWY3DPEHPK3PXP",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await test_session.execute(stmt)
        user_id = result.inserted_primary_key[0]
        await test_session.commit()

        # Create a device verification for a different device
        device_verification = MfaDeviceVerification(
            user_id=user_id,
            device_fingerprint="other_device_fingerprint",
            ip_address="127.0.0.1",
            user_agent="OtherBrowser/1.0",
            verified_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            mfa_method="totp",
        )
        test_session.add(device_verification)
        await test_session.commit()

        # Mock device fingerprint generation for current device
        with patch(
            "app.services.mfa_device_service.generate_device_fingerprint",
            return_value="current_device_fingerprint",
        ):

            login_data = {
                "email": user_email,
                "password": user_password,
                # No TOTP code provided
            }

            response = await test_client.post(
                "/api/auth/login",
                json=login_data,
                headers={
                    "X-Tenant-ID": "default",
                    "User-Agent": "CurrentBrowser/1.0",
                },
            )

        # Should require MFA for new device
        assert response.status_code == 400
        response_data = response.json()
        assert "TOTP code required" in response_data["detail"]

    @pytest.mark.asyncio
    async def test_account_locked_error_message(
        self, test_client, test_session, relax_auth_rate_limit
    ):
        """Test that locked accounts show proper error message."""
        # Create a locked user
        user_email = "locked_user@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Locked User",
            status="active",
            is_verified=True,
            failed_login_attempts=10,
            locked_until=datetime.now(timezone.utc) + timedelta(hours=1),  # Locked
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        login_data = {
            "email": user_email,
            "password": user_password,
        }

        response = await test_client.post(
            "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
        )

        # Should return account locked error
        assert response.status_code == 423
        response_data = response.json()
        assert response_data["detail"] == "account_locked"
