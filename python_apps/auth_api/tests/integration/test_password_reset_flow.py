import pytest
from sqlalchemy import select
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


@pytest.mark.asyncio
class TestPasswordResetFlow:
    """Tests for the password reset flow."""

    @patch("app.services.email_service.send_password_reset_email_with_new_password")
    async def test_forgot_password_endpoint(
        self, mock_send_email, test_client, test_user
    ):
        """Test the forgot-password endpoint."""
        # Setup mock
        mock_send_email.return_value = True

        # Get the test user's email
        user_email = test_user["email"]

        # Call the forgot-password endpoint
        response = await test_client.post(
            "/api/auth/forgot-password", json={"email": user_email}
        )

        # Check response
        assert response.status_code == 200
        assert (
            response.json()["message"]
            == "If your email is registered, you will receive a password reset email"
        )

        # Check that the email was sent
        assert mock_send_email.called
        call_args = mock_send_email.call_args[0]
        assert call_args[0] == user_email  # Email

        # The second argument should be the name extracted from full_name
        if test_user.get("full_name"):
            expected_name = test_user["full_name"].split()[0]
            assert call_args[1] == expected_name

        # The third argument should be the new password
        assert len(call_args[2]) >= 12  # New password should be at least 12 chars

    @patch("app.services.email_service.send_password_reset_email_with_new_password")
    async def test_forgot_password_nonexistent_user(self, mock_send_email, test_client):
        """Test the forgot-password endpoint with a nonexistent user."""
        # Call the forgot-password endpoint with a nonexistent email
        response = await test_client.post(
            "/api/auth/forgot-password", json={"email": "nonexistent@example.com"}
        )

        # Check response - should still return 200 for security reasons
        assert response.status_code == 200
        assert (
            response.json()["message"]
            == "If your email is registered, you will receive a password reset email"
        )

        # Check that no email was sent
        assert not mock_send_email.called

    @patch("app.services.email_service.send_password_reset_email_with_new_password")
    async def test_password_reset_flow_complete(
        self, mock_send_email, test_client, test_user, test_session_factory
    ):
        """Test the complete password reset flow."""
        # Setup mock
        mock_send_email.return_value = True

        # Get the test user's email
        user_email = test_user["email"]

        # Step 1: Call the forgot-password endpoint
        response = await test_client.post(
            "/api/auth/forgot-password", json={"email": user_email}
        )

        # Check response
        assert response.status_code == 200

        # Step 2: Verify that the user's password was changed and is_password_temporary is set
        session: AsyncSession = test_session_factory()
        try:
            result = await session.execute(select(User).where(User.email == user_email))
            user = result.scalars().first()
            assert user

            # After forgot-password, we expect a temporary password to be set with an expiry
            assert user.temporary_hashed_password is not None
            assert user.temporary_password_expiry is not None

            # Check that password_reset_token is None (direct reset, not token-based)
            assert user.password_reset_token is None

            # Get the new password from the mock call
            new_password = mock_send_email.call_args[0][2]

            # Step 3: Try to login with the new password
            login_response = await test_client.post(
                "/api/auth/login", json={"email": user_email, "password": new_password}
            )

            # Check login response
            assert login_response.status_code == 200
            login_data = login_response.json()

            # Check that we got tokens
            assert "access_token" in login_data
            assert "refresh_token" in login_data

            # Check that password_change_required is True
            assert login_data.get("password_change_required") is True

        finally:
            await session.close()

    async def test_test_credentials_trigger_password_reset(self, test_client):
        """Test that the test credentials trigger the password reset flow."""
        # Create a test user with temporary password
        from sqlalchemy import text
        from app.db.orm import get_async_session
        from app.core.security import get_password_hash
        from db_core.middleware import set_current_tenant_id
        from db_core.utils import get_schema_name
        from app.core.multitenancy import multitenancy_settings

        test_email = "panagiotis.v@iopex.com"
        test_password = "password123"

        # Create the user in the database
        async for session in get_async_session():
            # Set tenant context
            set_current_tenant_id("default")
            schema_name = get_schema_name("default", multitenancy_settings)
            await session.execute(text(f'SET search_path TO "{schema_name}", public'))

            # Check if user already exists
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": test_email}
            )
            user = result.scalar_one_or_none()

            if not user:
                # Create the user
                hashed_password = get_password_hash(test_password)
                await session.execute(
                    text(
                        """
                    INSERT INTO users (email, hashed_password, full_name, status, is_verified,
                                      is_superuser, is_manager, mfa_enabled, failed_login_attempts,
                                      is_password_temporary, application_admin, sms_mfa_enabled, phone_verified, email_mfa_enabled, biometric_mfa_enabled, created_at, updated_at)
                    VALUES (:email, :password, 'Test User', 'active', TRUE,
                           FALSE, FALSE, FALSE, 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW())
                    """
                    ),
                    {
                        "email": test_email,
                        "password": hashed_password,
                    },
                )
                await session.commit()

            await session.close()

        # Try to login with test credentials
        login_response = await test_client.post(
            "/api/auth/login",
            json={"email": test_email, "password": test_password},
        )

        # Check login response
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_data = login_response.json()

        # Check that we got tokens
        assert "access_token" in login_data
        assert "refresh_token" in login_data

        # Check that password_change_required is True
        assert login_data.get("password_change_required") is True
