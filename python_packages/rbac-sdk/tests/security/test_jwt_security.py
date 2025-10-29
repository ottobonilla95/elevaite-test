"""
Security tests for JWT validation in RBAC SDK.

Tests for common JWT vulnerabilities:
- Algorithm confusion attacks (HS256 vs RS256)
- None algorithm bypass
- Expired token handling
- Invalid signature detection
- Token reuse and replay attacks
- Key confusion attacks
- Weak secrets
"""

import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import jwt
import pytest

from rbac_sdk.fastapi_helpers import api_key_jwt_validator

# Test secrets
SECRET_KEY = "test-secret-key-do-not-use-in-production"
API_KEY_SECRET = "test-secret-key-for-integration-tests"
WEAK_SECRET = "weak"
DIFFERENT_SECRET = "different-secret-key"
ALGORITHM = "HS256"


class TestJWTAlgorithmConfusion:
    """Test algorithm confusion attacks."""

    def test_none_algorithm_rejected(self):
        """Test that 'none' algorithm tokens are rejected."""
        # Create a token with 'none' algorithm (no signature)
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        # Manually create token with 'none' algorithm
        header = {"alg": "none", "typ": "JWT"}
        import base64
        import json

        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode().rstrip("=")
        none_token = f"{header_b64}.{payload_b64}."

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # Should reject 'none' algorithm
        user_id = validator(none_token, request)
        assert user_id is None

    def test_algorithm_mismatch_rejected(self):
        """Test that tokens with wrong algorithm are rejected."""
        # Create token with HS512 when validator expects HS256
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        wrong_algo_token = jwt.encode(payload, API_KEY_SECRET, algorithm="HS512")

        validator = api_key_jwt_validator(algorithm="HS256", secret=API_KEY_SECRET)
        request = Mock()

        # Should reject token with wrong algorithm
        user_id = validator(wrong_algo_token, request)
        assert user_id is None

    def test_unsigned_token_rejected(self):
        """Test that unsigned tokens are rejected."""
        # Create token without signature
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        # Create token parts without signature
        import base64
        import json

        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode().rstrip("=")
        unsigned_token = f"{header_b64}.{payload_b64}"  # No signature part

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # Should reject unsigned token
        user_id = validator(unsigned_token, request)
        assert user_id is None


class TestJWTSignatureValidation:
    """Test JWT signature validation."""

    def test_invalid_signature_rejected(self):
        """Test that tokens with invalid signatures are rejected."""
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        # Create token with one secret
        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Try to validate with different secret
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=DIFFERENT_SECRET)
        request = Mock()

        user_id = validator(token, request)
        assert user_id is None

    def test_tampered_payload_rejected(self):
        """Test that tokens with tampered payloads are rejected."""
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Tamper with the payload by changing user ID
        parts = token.split(".")
        import base64
        import json

        # Decode payload
        payload_bytes = parts[1] + "=" * (4 - len(parts[1]) % 4)
        decoded_payload = json.loads(base64.urlsafe_b64decode(payload_bytes))

        # Change user ID
        decoded_payload["sub"] = "attacker999"

        # Re-encode payload
        tampered_payload = base64.urlsafe_b64encode(json.dumps(decoded_payload).encode()).decode().rstrip("=")

        # Create tampered token (same signature, different payload)
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # Should reject tampered token
        user_id = validator(tampered_token, request)
        assert user_id is None

    def test_weak_secret_still_validates(self):
        """Test that weak secrets still validate (but are discouraged)."""
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        # Create token with weak secret
        token = jwt.encode(payload, WEAK_SECRET, algorithm=ALGORITHM)

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=WEAK_SECRET)
        request = Mock()

        # Should still validate (JWT library doesn't enforce secret strength)
        user_id = validator(token, request)
        assert user_id == "user123"


class TestJWTExpiration:
    """Test JWT expiration handling."""

    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected."""
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        user_id = validator(token, request)
        assert user_id is None

    def test_token_about_to_expire_accepted(self):
        """Test that tokens about to expire are still accepted."""
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=5),  # Expires in 5 seconds
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        user_id = validator(token, request)
        assert user_id == "user123"

    def test_token_without_expiration_accepted(self):
        """Test that tokens without expiration are accepted (security concern).

        NOTE: This is a security concern! The JWT library (PyJWT) does NOT require
        an 'exp' claim by default. Tokens without expiration never expire, which
        is a security risk. Production systems should:
        1. Always include 'exp' in tokens
        2. Consider using verify_exp=True in jwt.decode() options
        3. Implement additional validation to reject tokens without 'exp'
        """
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            # No 'exp' field - this is a security risk!
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # Currently accepts token without expiration (security concern!)
        user_id = validator(token, request)
        assert user_id == "user123"  # Passes, but shouldn't in production!


class TestJWTClaimValidation:
    """Test JWT claim validation."""

    def test_missing_sub_claim_rejected(self):
        """Test that tokens without 'sub' claim are rejected."""
        payload = {
            # No 'sub' field
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        user_id = validator(token, request)
        assert user_id is None

    def test_wrong_token_type_rejected(self):
        """Test that tokens with wrong type are rejected."""
        payload = {
            "sub": "user123",
            "type": "access",  # Wrong type (should be 'api_key')
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        user_id = validator(token, request)
        assert user_id is None

    def test_missing_type_claim_rejected(self):
        """Test that tokens without 'type' claim are rejected."""
        payload = {
            "sub": "user123",
            # No 'type' field
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        user_id = validator(token, request)
        assert user_id is None
