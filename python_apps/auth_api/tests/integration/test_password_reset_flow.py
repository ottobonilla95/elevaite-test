import pytest
from unittest.mock import patch


@pytest.mark.asyncio
class TestPasswordResetFlow:
    """Tests for the password reset flow."""

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
