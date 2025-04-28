"""Unit tests for token schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.token import Token, TokenPayload


class TestTokenSchema:
    """Tests for the Token schema."""

    def test_valid_token(self):
        """Test that a valid token passes validation."""
        token_data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            "token_type": "bearer",
        }
        token = Token(**token_data)
        assert token.access_token == token_data["access_token"]
        assert token.token_type == token_data["token_type"]

    def test_missing_access_token(self):
        """Test that a missing access_token fails validation."""
        token_data = {
            "token_type": "bearer",
        }
        with pytest.raises(ValidationError):
            Token(**token_data)

    def test_missing_token_type(self):
        """Test that a missing token_type fails validation."""
        token_data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        }
        with pytest.raises(ValidationError):
            Token(**token_data)


class TestTokenPayloadSchema:
    """Tests for the TokenPayload schema."""

    def test_valid_token_payload(self):
        """Test that a valid token payload passes validation."""
        payload_data = {
            "sub": "123",
            "exp": 1516239022,
        }
        payload = TokenPayload(**payload_data)
        assert payload.sub == payload_data["sub"]
        assert payload.exp == payload_data["exp"]

    def test_missing_subject(self):
        """Test that a missing subject fails validation."""
        payload_data = {
            "exp": 1516239022,
        }
        with pytest.raises(ValidationError):
            TokenPayload(**payload_data)

    def test_missing_expiration(self):
        """Test that a missing expiration fails validation."""
        payload_data = {
            "sub": "123",
        }
        with pytest.raises(ValidationError):
            TokenPayload(**payload_data)

    def test_invalid_subject_type(self):
        """Test that an invalid subject type fails validation."""
        payload_data = {
            "sub": 123,  # Should be a string
            "exp": 1516239022,
        }
        with pytest.raises(ValidationError):
            TokenPayload(**payload_data)

    def test_invalid_expiration_type(self):
        """Test that an invalid expiration type fails validation."""
        payload_data = {
            "sub": "123",
            "exp": "1516239022",  # Should be an integer
        }
        with pytest.raises(ValidationError):
            TokenPayload(**payload_data)
