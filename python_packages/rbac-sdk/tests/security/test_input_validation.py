"""
Security tests for input validation - Phase 2.3.

Tests for SQL injection, XSS, integer overflow, type confusion,
null bytes, and unicode normalization.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from jose import jwt  # Use python-jose to match the validator

from rbac_sdk.fastapi_helpers import api_key_jwt_validator, api_key_http_validator

# Test configuration
API_KEY_SECRET = "test-secret-key-for-integration-tests"
ALGORITHM = "HS256"
AUTH_API_URL = "http://localhost:8004"


class TestSQLInjection:
    """Test SQL injection protection in validators."""

    def test_sql_injection_in_api_key(self):
        """Test that SQL injection attempts in API keys are handled safely."""
        validator = api_key_http_validator(
            base_url=AUTH_API_URL,
            cache_ttl=0,
        )
        request = Mock()

        # SQL injection attempts
        sql_injections = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "1' AND '1'='1",
        ]

        for injection in sql_injections:
            result = validator(injection, request)
            # Should be rejected (invalid key format)
            assert result is None, f"SQL injection not rejected: {injection}"

    def test_sql_injection_in_jwt_claims(self):
        """Test that SQL injection in JWT claims doesn't cause issues."""
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with SQL injection in claims
        payload = {
            "sub": "'; DROP TABLE users; --",
            "type": "api_key",
            "tenant_id": "' OR '1'='1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should validate successfully (JWT library handles encoding)
        user_id = validator(token, request)
        # Returns the malicious string, but it's just a string
        assert user_id == "'; DROP TABLE users; --"


class TestXSSProtection:
    """Test XSS (Cross-Site Scripting) protection."""

    def test_xss_in_api_key(self):
        """Test that XSS payloads in API keys are handled safely."""
        validator = api_key_http_validator(
            base_url=AUTH_API_URL,
            cache_ttl=0,
        )
        request = Mock()

        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>",
            "'-alert('XSS')-'",
        ]

        for payload in xss_payloads:
            result = validator(payload, request)
            # Should be rejected (invalid key format)
            assert result is None, f"XSS payload not rejected: {payload}"

    def test_xss_in_jwt_claims(self):
        """Test that XSS in JWT claims is properly encoded."""
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with XSS payload in claims
        payload = {
            "sub": "<script>alert('XSS')</script>",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should validate successfully (JWT library handles encoding)
        user_id = validator(token, request)
        # Returns the XSS string, but it's just a string
        assert user_id == "<script>alert('XSS')</script>"


class TestIntegerOverflow:
    """Test integer overflow protection."""

    def test_large_expiration_time(self):
        """Test that very large expiration times are handled safely."""
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with very large expiration (year 9999)
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": 253402300799,  # Max 32-bit timestamp (2038-01-19)
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should validate successfully (not expired)
        user_id = validator(token, request)
        assert user_id == "user123"

    def test_negative_expiration_time(self):
        """Test that negative expiration times are rejected."""
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with negative expiration
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": -1,
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should be rejected (expired)
        user_id = validator(token, request)
        assert user_id is None

    def test_zero_expiration_time(self):
        """Test that zero expiration time is rejected."""
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with zero expiration (epoch)
        payload = {
            "sub": "user123",
            "type": "api_key",
            "tenant_id": "default",
            "exp": 0,
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should be rejected (expired)
        user_id = validator(token, request)
        assert user_id is None


class TestTypeConfusion:
    """Test type confusion attacks."""

    def test_numeric_user_id(self):
        """Test that numeric user IDs are rejected.

        NOTE: python-jose validates that 'sub' must be a string.
        This is good security behavior - prevents type confusion attacks.
        """
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with numeric user ID
        payload = {
            "sub": 12345,  # Number instead of string
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should be rejected (python-jose requires sub to be a string)
        user_id = validator(token, request)
        assert user_id is None

    def test_boolean_user_id(self):
        """Test that boolean user IDs are rejected.

        NOTE: python-jose validates that 'sub' must be a string.
        This is good security behavior - prevents type confusion attacks.
        """
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with boolean user ID (True)
        payload = {
            "sub": True,  # Boolean instead of string
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should be rejected (python-jose requires sub to be a string)
        user_id = validator(token, request)
        assert user_id is None

    def test_array_user_id(self):
        """Test that array user IDs are rejected."""
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with array user ID
        payload = {
            "sub": ["user1", "user2"],  # Array instead of string
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should be rejected (invalid type)
        user_id = validator(token, request)
        assert user_id is None


class TestNullBytes:
    """Test null byte injection protection."""

    def test_null_byte_in_api_key(self):
        """Test that null bytes in API keys are handled safely."""
        validator = api_key_http_validator(
            base_url=AUTH_API_URL,
            cache_ttl=0,
        )
        request = Mock()

        # API key with null byte
        malicious_key = "valid-key\x00admin"

        result = validator(malicious_key, request)
        # Should be rejected (invalid format)
        assert result is None

    def test_null_byte_in_jwt_claims(self):
        """Test that null bytes in JWT claims are handled safely."""
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with null byte in claims
        payload = {
            "sub": "user123\x00admin",
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, API_KEY_SECRET, algorithm=ALGORITHM)

        # Should validate (JWT library handles encoding)
        user_id = validator(token, request)
        # Returns the string with null byte
        assert user_id == "user123\x00admin"


class TestUnicodeNormalization:
    """Test unicode normalization attacks."""

    def test_unicode_in_api_key(self):
        """Test that unicode characters in API keys are handled safely."""
        validator = api_key_http_validator(
            base_url=AUTH_API_URL,
            cache_ttl=0,
        )
        request = Mock()

        # API key with unicode characters
        unicode_keys = [
            "user123\u200b",  # Zero-width space
            "user123\ufeff",  # Zero-width no-break space
            "user\u0301123",  # Combining acute accent
            "user123\u202e",  # Right-to-left override
        ]

        for key in unicode_keys:
            result = validator(key, request)
            # Should be rejected (invalid format)
            assert result is None, f"Unicode key not rejected: {repr(key)}"

    def test_unicode_normalization_in_jwt(self):
        """Test that unicode normalization doesn't cause issues.

        NOTE: This test demonstrates a security concern. Unicode normalization
        can cause two visually identical strings to have different byte
        representations, potentially bypassing security checks or causing
        authorization issues.

        "é" can be represented as:
        - "\u00e9" (NFC - composed form)
        - "e\u0301" (NFD - decomposed form: e + combining acute accent)

        These look identical but are different strings!
        """
        validator = api_key_jwt_validator(algorithm=ALGORITHM, secret=API_KEY_SECRET)
        request = Mock()

        # JWT with unicode characters (NFC vs NFD normalization)
        payload1 = {
            "sub": "user\u00e9",  # NFC form
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        payload2 = {
            "sub": "user\u0065\u0301",  # NFD form (same visual character, different encoding)
            "type": "api_key",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token1 = jwt.encode(payload1, API_KEY_SECRET, algorithm=ALGORITHM)
        token2 = jwt.encode(payload2, API_KEY_SECRET, algorithm=ALGORITHM)

        user_id1 = validator(token1, request)
        user_id2 = validator(token2, request)

        # Both should validate
        assert user_id1 is not None
        assert user_id2 is not None

        # They're both valid strings
        assert isinstance(user_id1, str)
        assert isinstance(user_id2, str)

        # But they're not equal as strings (different byte representations)
        assert user_id1 != user_id2, "Unicode normalization issue: NFC != NFD"

        # This could cause authorization bypass if user IDs are compared without normalization
        print(f"\nNFC: {repr(user_id1)}")
        print(f"NFD: {repr(user_id2)}")
        print(f"Visually identical but different: {user_id1 == user_id2}")
