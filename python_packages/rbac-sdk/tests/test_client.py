"""
Brutal unit tests for rbac_sdk.client (synchronous client).

These tests cover:
- Happy path scenarios
- Network failures and timeouts
- Malformed responses
- Edge cases and boundary conditions
- Security concerns
"""

import pytest
import requests
from unittest.mock import patch, Mock
from rbac_sdk.client import check_access, RBACClientError, DEFAULT_AUTHZ_SERVICE_URL


class TestCheckAccessHappyPath:
    """Test successful authorization checks."""

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_allowed(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that check_access returns True when allowed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}
        mock_post.return_value = mock_response

        result = check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == f"{DEFAULT_AUTHZ_SERVICE_URL}/api/authz/check_access"
        assert call_args[1]["json"]["user_id"] == sample_user_id
        assert call_args[1]["json"]["action"] == sample_action
        assert call_args[1]["json"]["resource"] == sample_resource

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_denied(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that check_access returns False when denied."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "allowed": False,
            "deny_reason": "insufficient_permissions",
        }
        mock_post.return_value = mock_response

        result = check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_with_custom_base_url(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that custom base_url is used correctly."""
        custom_url = "http://custom-auth-api:9000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}
        mock_post.return_value = mock_response

        check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
            base_url=custom_url,
        )

        call_args = mock_post.call_args
        assert call_args[0][0] == f"{custom_url}/api/authz/check_access"

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_strips_trailing_slash(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that trailing slashes in base_url are handled correctly."""
        custom_url = "http://custom-auth-api:9000/"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}
        mock_post.return_value = mock_response

        check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
            base_url=custom_url,
        )

        call_args = mock_post.call_args
        # Should not have double slash
        assert call_args[0][0] == "http://custom-auth-api:9000/api/authz/check_access"


class TestCheckAccessNetworkFailures:
    """Test network failure scenarios - these should raise RBACClientError."""

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_connection_error(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that connection errors raise RBACClientError."""
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        with pytest.raises(RBACClientError) as exc_info:
            check_access(
                user_id=sample_user_id,
                action=sample_action,
                resource=sample_resource,
            )

        assert "AuthZ service call failed" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_timeout(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that timeouts raise RBACClientError."""
        mock_post.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(RBACClientError) as exc_info:
            check_access(
                user_id=sample_user_id,
                action=sample_action,
                resource=sample_resource,
                timeout=1.0,
            )

        assert "AuthZ service call failed" in str(exc_info.value)

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_http_error_404(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that 404 errors raise RBACClientError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        with pytest.raises(RBACClientError):
            check_access(
                user_id=sample_user_id,
                action=sample_action,
                resource=sample_resource,
            )

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_http_error_500(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that 500 errors raise RBACClientError."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "500 Internal Server Error"
        )
        mock_post.return_value = mock_response

        with pytest.raises(RBACClientError):
            check_access(
                user_id=sample_user_id,
                action=sample_action,
                resource=sample_resource,
            )

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_http_error_401(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that 401 errors raise RBACClientError."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "401 Unauthorized"
        )
        mock_post.return_value = mock_response

        with pytest.raises(RBACClientError):
            check_access(
                user_id=sample_user_id,
                action=sample_action,
                resource=sample_resource,
            )


class TestCheckAccessMalformedResponses:
    """Test handling of malformed or unexpected responses."""

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_missing_allowed_field(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that missing 'allowed' field defaults to False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "deny_reason": "some_reason"
        }  # Missing 'allowed'
        mock_post.return_value = mock_response

        result = check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        # Should default to False when 'allowed' is missing
        assert result is False

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_empty_response(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that empty JSON response defaults to False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        result = check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_invalid_json(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that invalid JSON raises RBACClientError."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Invalid JSON", "", 0
        )
        mock_post.return_value = mock_response

        with pytest.raises(RBACClientError):
            check_access(
                user_id=sample_user_id,
                action=sample_action,
                resource=sample_resource,
            )

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_allowed_null(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that null 'allowed' value is treated as False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": None}
        mock_post.return_value = mock_response

        result = check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_allowed_string_true(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that string 'true' is converted to boolean True."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": "true"}
        mock_post.return_value = mock_response

        result = check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        # bool("true") is True in Python
        assert result is True

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_allowed_string_false(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that string 'false' is converted to boolean True (non-empty string)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": "false"}
        mock_post.return_value = mock_response

        result = check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        # bool("false") is True in Python (non-empty string) - this is a potential bug!
        assert result is True


class TestCheckAccessEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_zero_user_id(self, mock_post, sample_action, sample_resource):
        """Test that user_id=0 is handled correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}
        mock_post.return_value = mock_response

        result = check_access(
            user_id=0,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is True
        call_args = mock_post.call_args
        assert call_args[1]["json"]["user_id"] == 0

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_negative_user_id(
        self, mock_post, sample_action, sample_resource
    ):
        """Test that negative user_id is sent (validation should be server-side)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": False}
        mock_post.return_value = mock_response

        check_access(
            user_id=-1,
            action=sample_action,
            resource=sample_resource,
        )

        call_args = mock_post.call_args
        assert call_args[1]["json"]["user_id"] == -1

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_empty_action(
        self, mock_post, sample_user_id, sample_resource
    ):
        """Test that empty action string is sent (validation should be server-side)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": False}
        mock_post.return_value = mock_response

        check_access(
            user_id=sample_user_id,
            action="",
            resource=sample_resource,
        )

        call_args = mock_post.call_args
        assert call_args[1]["json"]["action"] == ""

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_empty_resource(
        self, mock_post, sample_user_id, sample_action
    ):
        """Test that empty resource dict is sent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": False}
        mock_post.return_value = mock_response

        check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource={},
        )

        call_args = mock_post.call_args
        assert call_args[1]["json"]["resource"] == {}

    @patch("rbac_sdk.client.requests.post")
    def test_check_access_custom_timeout(
        self, mock_post, sample_user_id, sample_action, sample_resource
    ):
        """Test that custom timeout is passed to requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}
        mock_post.return_value = mock_response

        check_access(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
            timeout=10.0,
        )

        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 10.0
