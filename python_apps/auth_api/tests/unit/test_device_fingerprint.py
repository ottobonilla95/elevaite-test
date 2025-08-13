import pytest
from unittest.mock import Mock
from fastapi import Request

from app.core.device_fingerprint import (
    generate_device_fingerprint,
    get_client_ip,
    is_device_fingerprint_valid,
    get_device_info_for_logging,
    extract_platform_from_user_agent,
)

pytestmark = [pytest.mark.unit, pytest.mark.mfa]


class TestDeviceFingerprinting:
    """Test device fingerprinting functionality."""

    def _create_mock_request(self, headers_dict=None, client_host="192.168.1.100"):
        """Helper to create a properly mocked request object."""
        request = Mock(spec=Request)
        headers_dict = headers_dict or {}
        request.headers = Mock()
        request.headers.get = lambda key, default=None: headers_dict.get(key, default)

        if client_host:
            request.client = Mock()
            request.client.host = client_host
        else:
            request.client = None

        return request

    def test_generate_device_fingerprint_basic(self):
        """Test basic device fingerprint generation."""
        headers_dict = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.5",
            "accept-encoding": "gzip, deflate",
            "x-forwarded-for": "192.168.1.100",
        }
        request = self._create_mock_request(headers_dict)

        user_id = 123
        fingerprint = generate_device_fingerprint(request, user_id)

        # Should return a SHA256 hash (64 characters)
        assert len(fingerprint) == 64
        assert isinstance(fingerprint, str)
        assert fingerprint.isalnum()

    def test_generate_device_fingerprint_consistency(self):
        """Test that same inputs produce same fingerprint."""
        headers_dict = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/html,application/xhtml+xml",
            "accept-language": "en-US,en;q=0.5",
            "accept-encoding": "gzip, deflate",
        }
        request = self._create_mock_request(headers_dict)

        user_id = 123

        # Generate fingerprint twice
        fingerprint1 = generate_device_fingerprint(request, user_id)
        fingerprint2 = generate_device_fingerprint(request, user_id)

        # Should be identical
        assert fingerprint1 == fingerprint2

    def test_generate_device_fingerprint_different_users(self):
        """Test that different users produce different fingerprints."""
        headers_dict = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/html,application/xhtml+xml",
        }
        request = self._create_mock_request(headers_dict)

        # Generate fingerprints for different users
        fingerprint1 = generate_device_fingerprint(request, 123)
        fingerprint2 = generate_device_fingerprint(request, 456)

        # Should be different
        assert fingerprint1 != fingerprint2

    def test_generate_device_fingerprint_different_browsers(self):
        """Test that different browsers produce different fingerprints."""
        user_id = 123

        # Chrome request
        chrome_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        chrome_request = self._create_mock_request(chrome_headers)

        # Firefox request
        firefox_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        }
        firefox_request = self._create_mock_request(firefox_headers)

        # Generate fingerprints
        chrome_fingerprint = generate_device_fingerprint(chrome_request, user_id)
        firefox_fingerprint = generate_device_fingerprint(firefox_request, user_id)

        # Should be different
        assert chrome_fingerprint != firefox_fingerprint

    def test_get_client_ip_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header."""
        headers_dict = {"x-forwarded-for": "203.0.113.1, 192.168.1.100, 10.0.0.1"}
        request = self._create_mock_request(headers_dict)

        ip = get_client_ip(request)
        assert ip == "203.0.113.1"  # Should return the first IP

    def test_get_client_ip_x_real_ip(self):
        """Test IP extraction from X-Real-IP header."""
        headers_dict = {"x-real-ip": "203.0.113.1"}
        request = self._create_mock_request(headers_dict)

        ip = get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_direct(self):
        """Test IP extraction from direct client connection."""
        request = self._create_mock_request({}, "192.168.1.100")

        ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_fallback(self):
        """Test IP extraction fallback when no client info available."""
        request = self._create_mock_request({}, "")

        ip = get_client_ip(request)
        assert ip == "unknown"

    def test_is_device_fingerprint_valid_exact_match(self):
        """Test fingerprint validation with exact match."""
        fingerprint = "abc123def456"
        assert is_device_fingerprint_valid(fingerprint, fingerprint) is True

    def test_is_device_fingerprint_valid_no_match(self):
        """Test fingerprint validation with no match."""
        fingerprint1 = "abc123def456"
        fingerprint2 = "xyz789uvw012"
        assert is_device_fingerprint_valid(fingerprint1, fingerprint2) is False

    def test_get_device_info_for_logging(self):
        """Test device info extraction for logging."""
        headers_dict = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept-language": "en-US,en;q=0.5",
        }
        request = self._create_mock_request(headers_dict)

        device_info = get_device_info_for_logging(request)

        assert "user_agent" in device_info
        assert "ip_address" in device_info
        assert "accept_language" in device_info
        assert "platform" in device_info
        assert device_info["ip_address"] == "192.168.1.100"
        assert device_info["platform"] == "Windows"

    def test_extract_platform_from_user_agent_windows(self):
        """Test platform extraction for Windows."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        platform = extract_platform_from_user_agent(user_agent)
        assert platform == "Windows"

    def test_extract_platform_from_user_agent_macos(self):
        """Test platform extraction for macOS."""
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        platform = extract_platform_from_user_agent(user_agent)
        assert platform == "macOS"

    def test_extract_platform_from_user_agent_linux(self):
        """Test platform extraction for Linux."""
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        platform = extract_platform_from_user_agent(user_agent)
        assert platform == "Linux"

    def test_extract_platform_from_user_agent_android(self):
        """Test platform extraction for Android."""
        user_agent = "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36"
        platform = extract_platform_from_user_agent(user_agent)
        assert platform == "Android"

    def test_extract_platform_from_user_agent_ios(self):
        """Test platform extraction for iOS."""
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15"
        platform = extract_platform_from_user_agent(user_agent)
        assert platform == "iOS"

    def test_extract_platform_from_user_agent_unknown(self):
        """Test platform extraction for unknown user agent."""
        user_agent = "SomeCustomBot/1.0"
        platform = extract_platform_from_user_agent(user_agent)
        assert platform == "Unknown"

    def test_generate_device_fingerprint_with_additional_data(self):
        """Test device fingerprint generation with additional data."""
        headers_dict = {"user-agent": "TestAgent/1.0"}
        request = self._create_mock_request(headers_dict)

        user_id = 123
        additional_data = "custom_data"

        # Generate fingerprints with and without additional data
        fingerprint1 = generate_device_fingerprint(request, user_id)
        fingerprint2 = generate_device_fingerprint(request, user_id, additional_data)

        # Should be different
        assert fingerprint1 != fingerprint2

    def test_generate_device_fingerprint_missing_headers(self):
        """Test device fingerprint generation with missing headers."""
        request = self._create_mock_request({}, "")  # No headers, no client info

        user_id = 123
        fingerprint = generate_device_fingerprint(request, user_id)

        # Should still generate a valid fingerprint
        assert len(fingerprint) == 64
        assert isinstance(fingerprint, str)
        assert fingerprint.isalnum()
