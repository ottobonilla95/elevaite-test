import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import asyncio

from app.db.models import User
from app.core.security import get_password_hash

pytestmark = [pytest.mark.integration, pytest.mark.security]


class TestSecurityImprovements:
    """Integration tests for security improvements."""

    @pytest.mark.asyncio
    async def test_progressive_account_lockout(self, test_client, test_session):
        """Test progressive account lockout mechanism."""
        # Create a user
        user_email = "lockout_test@example.com"
        user_password = "Password123!@#"
        wrong_password = "WrongPassword123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Lockout Test User",
            status="active",
            is_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        # Test progressive lockout
        login_data = {
            "email": user_email,
            "password": wrong_password,
        }

        # First 4 failed attempts should not lock the account
        for i in range(4):
            response = await test_client.post(
                "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
            )
            assert response.status_code == 401
            assert "Incorrect email or password" in response.json()["detail"]

        # 5th failed attempt should lock the account for 5 minutes
        response = await test_client.post(
            "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
        )
        assert response.status_code == 423
        assert response.json()["detail"] == "account_locked"

        # Verify subsequent login attempts are blocked even with correct password
        correct_login_data = {
            "email": user_email,
            "password": user_password,
        }
        response = await test_client.post(
            "/api/auth/login",
            json=correct_login_data,
            headers={"X-Tenant-ID": "default"},
        )
        assert response.status_code == 423
        assert response.json()["detail"] == "account_locked"

    @pytest.mark.asyncio
    async def test_account_lockout_escalation(self, test_client, test_session):
        """Test that lockout duration escalates with more failures."""
        # Create a user with existing failed attempts
        user_email = "escalation_test@example.com"
        user_password = "Password123!@#"
        wrong_password = "WrongPassword123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Escalation Test User",
            status="active",
            is_verified=True,
            failed_login_attempts=9,  # Already has 9 failed attempts
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        # One more failed attempt should trigger 15-minute lockout
        login_data = {
            "email": user_email,
            "password": wrong_password,
        }

        response = await test_client.post(
            "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
        )
        assert response.status_code == 423
        assert response.json()["detail"] == "account_locked"

        # Verify user is locked
        from sqlalchemy import select

        stmt = select(User).where(User.email == user_email)
        result = await test_session.execute(stmt)
        user = result.scalars().first()

        assert user.failed_login_attempts == 10
        assert user.locked_until is not None
        assert user.locked_until > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_successful_login_resets_failed_attempts(
        self, test_client, test_session
    ):
        """Test that successful login resets failed login attempts."""
        # Create a user with some failed attempts
        user_email = "reset_test@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Reset Test User",
            status="active",
            is_verified=True,
            failed_login_attempts=3,  # Has some failed attempts
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        # Successful login
        login_data = {
            "email": user_email,
            "password": user_password,
        }

        response = await test_client.post(
            "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
        )
        assert response.status_code == 200

        # Verify failed attempts were reset
        from sqlalchemy import select

        stmt = select(User).where(User.email == user_email)
        result = await test_session.execute(stmt)
        user = result.scalars().first()

        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    @pytest.mark.asyncio
    async def test_rate_limiting_login_endpoint(self, test_client, test_session):
        """Test rate limiting on login endpoint."""
        # Create a user
        user_email = "ratelimit_test@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Rate Limit Test User",
            status="active",
            is_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        login_data = {
            "email": user_email,
            "password": "wrong_password",
        }

        # Make requests up to the rate limit (5 per minute for login)
        responses = []
        for i in range(6):  # Try 6 requests (should hit rate limit)
            response = await test_client.post(
                "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
            )
            responses.append(response)

            # Small delay to avoid overwhelming the test
            await asyncio.sleep(0.1)

        # First 5 should be normal auth failures (401)
        for i in range(5):
            assert responses[i].status_code == 401

        # 6th should be rate limited (429)
        assert responses[5].status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limiting_password_reset_endpoint(self, test_client):
        """Test rate limiting on password reset endpoint."""
        reset_data = {
            "email": "test@example.com",
        }

        # Make requests up to the rate limit (3 per minute for password reset)
        responses = []
        for i in range(4):  # Try 4 requests (should hit rate limit)
            response = await test_client.post(
                "/api/auth/forgot-password",
                json=reset_data,
                headers={"X-Tenant-ID": "default"},
            )
            responses.append(response)

            # Small delay to avoid overwhelming the test
            await asyncio.sleep(0.1)

        # First 3 should be successful (200)
        for i in range(3):
            assert responses[i].status_code == 200

        # 4th should be rate limited (429)
        assert responses[3].status_code == 429

    @pytest.mark.asyncio
    async def test_password_reset_for_locked_account_with_logging(
        self, test_client, test_session
    ):
        """Test password reset for locked account includes proper logging."""
        # Create a locked user
        user_email = "locked_reset@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Locked Reset User",
            status="active",
            is_verified=True,
            failed_login_attempts=10,
            locked_until=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        with patch("app.routers.auth.logger") as mock_logger:
            reset_data = {
                "email": user_email,
            }

            response = await test_client.post(
                "/api/auth/forgot-password",
                json=reset_data,
                headers={"X-Tenant-ID": "default"},
            )

            # Should still allow password reset
            assert response.status_code == 200

            # Verify warning was logged
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Password reset requested for locked account" in warning_call
            assert user_email in warning_call

    @pytest.mark.asyncio
    async def test_duplicate_password_reset_prevention(self, test_client, test_session):
        """Test that duplicate password reset requests are prevented."""
        # Create a user with active password reset
        user_email = "duplicate_reset@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Duplicate Reset User",
            status="active",
            is_verified=True,
            password_reset_expires=datetime.now(timezone.utc)
            + timedelta(hours=1),  # Active reset
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        reset_data = {
            "email": user_email,
        }

        # First request should be handled normally
        response = await test_client.post(
            "/api/auth/forgot-password",
            json=reset_data,
            headers={"X-Tenant-ID": "default"},
        )
        assert response.status_code == 200

        # Verify no new password reset was created (should return same message)
        response_data = response.json()
        assert "If your email is registered" in response_data["message"]

    @pytest.mark.asyncio
    async def test_account_lockout_logging(self, test_client, test_session):
        """Test that account lockout events are properly logged."""
        # Create a user
        user_email = "logging_test@example.com"
        user_password = "Password123!@#"
        wrong_password = "WrongPassword123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Logging Test User",
            status="active",
            is_verified=True,
            failed_login_attempts=4,  # One away from lockout
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        with patch("app.services.auth_orm.logger") as mock_logger:
            login_data = {
                "email": user_email,
                "password": wrong_password,
            }

            # This should trigger account lockout
            response = await test_client.post(
                "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
            )

            assert response.status_code == 423

            # Verify lockout was logged
            mock_logger.warning.assert_called()
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]

            # Should log both password failure and account lockout
            assert any("Password verification failed" in call for call in warning_calls)
            assert any("Account locked for user" in call for call in warning_calls)

    @pytest.mark.asyncio
    async def test_locked_account_login_attempt_logging(
        self, test_client, test_session
    ):
        """Test that login attempts on locked accounts are logged."""
        # Create a locked user
        user_email = "locked_attempt@example.com"
        user_password = "Password123!@#"
        hashed_password = get_password_hash(user_password)

        from sqlalchemy import insert

        stmt = insert(User).values(
            email=user_email,
            hashed_password=hashed_password,
            full_name="Locked Attempt User",
            status="active",
            is_verified=True,
            failed_login_attempts=10,
            locked_until=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await test_session.execute(stmt)
        await test_session.commit()

        with patch("app.services.auth_orm.logger") as mock_logger:
            login_data = {
                "email": user_email,
                "password": user_password,
            }

            response = await test_client.post(
                "/api/auth/login", json=login_data, headers={"X-Tenant-ID": "default"}
            )

            assert response.status_code == 423

            # Verify blocked login attempt was logged
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Login attempt blocked - Account locked" in warning_call
            assert user_email in warning_call
