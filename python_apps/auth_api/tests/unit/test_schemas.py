"""Unit tests for schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.user import (
    UserCreate,
    PasswordUpdate,
    LoginRequest,
    UserResponse,
    SessionInfo,
)


class TestUserCreateSchema:
    """Tests for the UserCreate schema."""

    def test_valid_user_create(self):
        """Test that a valid user creation schema passes validation."""
        user_data = {
            "email": "test@example.com",
            "password": "Password123!@#",
            "full_name": "Test User",
        }
        user = UserCreate(**user_data)
        assert user.email == user_data["email"]
        assert user.password == user_data["password"]
        assert user.full_name == user_data["full_name"]

    def test_invalid_email(self):
        """Test that an invalid email fails validation."""
        user_data = {
            "email": "invalid-email",
            "password": "Password123!@#",
            "full_name": "Test User",
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_password_too_short(self):
        """Test that a password that's too short fails validation."""
        user_data = {
            "email": "test@example.com",
            "password": "Short1!",
            "full_name": "Test User",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "String should have at least 9 characters" in str(exc_info.value)

    def test_password_no_lowercase(self):
        """Test that a password without lowercase letters fails validation."""
        user_data = {
            "email": "test@example.com",
            "password": "PASSWORD123!@#",
            "full_name": "Test User",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "Password must contain at least one lowercase letter" in str(
            exc_info.value
        )

    def test_password_no_uppercase(self):
        """Test that a password without uppercase letters fails validation."""
        user_data = {
            "email": "test@example.com",
            "password": "password123!@#",
            "full_name": "Test User",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "Password must contain at least one uppercase letter" in str(
            exc_info.value
        )

    def test_password_no_digit(self):
        """Test that a password without digits fails validation."""
        user_data = {
            "email": "test@example.com",
            "password": "Password!@#$%^",
            "full_name": "Test User",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "Password must contain at least one digit" in str(exc_info.value)

    def test_password_no_special_char(self):
        """Test that a password without special characters fails validation."""
        user_data = {
            "email": "test@example.com",
            "password": "Password123456",
            "full_name": "Test User",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "Password must contain at least one special character" in str(
            exc_info.value
        )

    def test_optional_full_name(self):
        """Test that full_name is optional."""
        user_data = {
            "email": "test@example.com",
            "password": "Password123!@#",
        }
        user = UserCreate(**user_data)
        assert user.email == user_data["email"]
        assert user.password == user_data["password"]
        assert user.full_name is None


class TestPasswordUpdateSchema:
    """Tests for the PasswordUpdate schema."""

    def test_valid_password_update(self):
        """Test that a valid password update schema passes validation."""
        password_data = {
            "current_password": "OldPassword123!@#",
            "new_password": "NewPassword123!@#",
        }
        password_update = PasswordUpdate(**password_data)
        assert password_update.current_password == password_data["current_password"]
        assert password_update.new_password == password_data["new_password"]

    def test_new_password_validation(self):
        """Test that the new password is validated."""
        password_data = {
            "current_password": "OldPassword123!@#",
            "new_password": "weak",
        }
        with pytest.raises(ValidationError):
            PasswordUpdate(**password_data)


class TestLoginRequestSchema:
    """Tests for the LoginRequest schema."""

    def test_valid_login_request(self):
        """Test that a valid login request schema passes validation."""
        login_data = {
            "email": "test@example.com",
            "password": "Password123!@#",
        }
        login_request = LoginRequest(**login_data)
        assert login_request.email == login_data["email"]
        assert login_request.password == login_data["password"]
        assert login_request.totp_code is None

    def test_login_with_totp(self):
        """Test login request with TOTP code."""
        login_data = {
            "email": "test@example.com",
            "password": "Password123!@#",
            "totp_code": "123456",
        }
        login_request = LoginRequest(**login_data)
        assert login_request.email == login_data["email"]
        assert login_request.password == login_data["password"]
        assert login_request.totp_code == login_data["totp_code"]

    def test_invalid_email(self):
        """Test that an invalid email fails validation."""
        login_data = {
            "email": "invalid-email",
            "password": "Password123!@#",
        }
        with pytest.raises(ValidationError):
            LoginRequest(**login_data)


class TestResponseSchemas:
    """Tests for response schemas."""

    def test_user_response_from_attributes(self):
        """Test that UserResponse can be created from an ORM model's attributes."""
        # Create a dict that mimics an ORM model's __dict__
        user_dict = {
            "id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "is_verified": True,
            "mfa_enabled": False,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
        }

        # This should work with from_attributes=True (formerly orm_mode=True)
        user_response = UserResponse.model_validate(user_dict)
        assert user_response.id == user_dict["id"]
        assert user_response.email == user_dict["email"]
        assert user_response.full_name == user_dict["full_name"]
        assert user_response.is_verified == user_dict["is_verified"]
        assert user_response.mfa_enabled == user_dict["mfa_enabled"]

    def test_session_info_from_attributes(self):
        """Test that SessionInfo can be created from an ORM model's attributes."""
        # Create a dict that mimics an ORM model's __dict__
        session_dict = {
            "id": 1,
            "ip_address": "127.0.0.1",
            "user_agent": "Test User Agent",
            "created_at": "2023-01-01T00:00:00",
            "expires_at": "2023-01-02T00:00:00",
            "is_current": True,
        }

        # This should work with from_attributes=True (formerly orm_mode=True)
        session_info = SessionInfo.model_validate(session_dict)
        assert session_info.id == session_dict["id"]
        assert session_info.ip_address == session_dict["ip_address"]
        assert session_info.user_agent == session_dict["user_agent"]
        assert session_info.is_current == session_dict["is_current"]
