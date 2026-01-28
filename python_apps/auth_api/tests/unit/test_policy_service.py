"""
Unit tests for PolicyService

Tests the OPA policy management service in isolation using mocked HTTP calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.policy_service import PolicyService, get_policy_service


class TestPolicyService:
    """Test PolicyService class"""

    @pytest.fixture
    def policy_service(self):
        """Create a PolicyService instance for testing"""
        with patch("app.services.policy_service.settings") as mock_settings:
            mock_settings.OPA_URL = "http://localhost:8181/v1/data/rbac/allow"
            service = PolicyService()
            return service

    @pytest.mark.asyncio
    async def test_init(self, policy_service):
        """Test PolicyService initialization"""
        assert policy_service.opa_base_url == "http://localhost:8181"
        assert policy_service.policy_base_url == "http://localhost:8181/v1/policies"

    @pytest.mark.asyncio
    async def test_upload_policy_success(self, policy_service):
        """Test successful policy upload"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.upload_policy(
                "rbac/test", "package rbac\n\nallow = true"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_upload_policy_failure(self, policy_service):
        """Test failed policy upload"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid policy"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.upload_policy("rbac/test", "invalid rego")

            assert result is False

    @pytest.mark.asyncio
    async def test_upload_policy_exception(self, policy_service):
        """Test policy upload with exception"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                side_effect=Exception("Connection error")
            )

            result = await policy_service.upload_policy("rbac/test", "package rbac")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_policy_success(self, policy_service):
        """Test successful policy retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"raw": "package rbac\n\nallow = true"}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.get_policy("rbac/test")

            assert result == "package rbac\n\nallow = true"

    @pytest.mark.asyncio
    async def test_get_policy_not_found(self, policy_service):
        """Test getting non-existent policy"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.get_policy("rbac/nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_policy_success(self, policy_service):
        """Test successful policy deletion"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.delete_policy("rbac/test")

            assert result is True

    @pytest.mark.asyncio
    async def test_delete_policy_failure(self, policy_service):
        """Test failed policy deletion"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.delete_policy("rbac/test")

            assert result is False

    @pytest.mark.asyncio
    async def test_list_policies_success(self, policy_service):
        """Test successful policy listing"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "rbac/core": {},
                "rbac/workflows": {},
                "rbac/agents": {},
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.list_policies()

            assert len(result) == 3
            assert {"id": "rbac/core", "name": "rbac/core"} in result
            assert {"id": "rbac/workflows", "name": "rbac/workflows"} in result

    @pytest.mark.asyncio
    async def test_list_policies_empty(self, policy_service):
        """Test listing policies when none exist"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await policy_service.list_policies()

            assert result == []

    @pytest.mark.asyncio
    async def test_validate_rego_syntax_valid(self, policy_service):
        """Test validating valid rego syntax"""
        # Mock successful upload (validation)
        upload_response = MagicMock()
        upload_response.status_code = 200

        # Mock successful deletion (cleanup)
        delete_response = MagicMock()
        delete_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=upload_response
            )
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=delete_response
            )

            is_valid, error = await policy_service.validate_rego_syntax(
                "package rbac\n\nallow = true"
            )

            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_rego_syntax_invalid(self, policy_service):
        """Test validating invalid rego syntax"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"errors": [{"message": "unexpected token"}]}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            is_valid, error = await policy_service.validate_rego_syntax("invalid rego")

            assert is_valid is False
            assert "unexpected token" in error

    @pytest.mark.asyncio
    async def test_generate_service_policy_basic(self, policy_service):
        """Test generating a basic service policy"""
        rego = await policy_service.generate_service_policy(
            service_name="workflow_engine",
            resource_type="workflow",
            actions={
                "admin": ["create_workflow", "edit_workflow", "view_workflow"],
                "viewer": ["view_workflow"],
            },
        )

        # Check that rego contains expected elements
        assert "package rbac" in rego
        assert "import rego.v1" in rego
        assert (
            "WORKFLOW ENGINE" in rego.upper()
        )  # Service name is converted to title case
        assert "workflow" in rego
        assert "create_workflow" in rego
        assert "edit_workflow" in rego
        assert "view_workflow" in rego
        assert "admin" in rego
        assert "viewer" in rego

    @pytest.mark.asyncio
    async def test_generate_service_policy_single_action(self, policy_service):
        """Test generating policy with single action per role"""
        rego = await policy_service.generate_service_policy(
            service_name="reports",
            resource_type="report",
            actions={"viewer": ["view_report"]},
        )

        assert "package rbac" in rego
        assert "view_report" in rego
        assert "viewer" in rego

    @pytest.mark.asyncio
    async def test_generate_service_policy_custom_belongs_to(self, policy_service):
        """Test generating policy with custom belongs_to"""
        rego = await policy_service.generate_service_policy(
            service_name="billing",
            resource_type="invoice",
            actions={"admin": ["create_invoice", "view_invoice"]},
            belongs_to="organization",
        )

        assert "package rbac" in rego
        assert "organization" in rego
        assert "organization_id" in rego
        assert "invoice" in rego

    @pytest.mark.asyncio
    async def test_generate_service_policy_empty_actions(self, policy_service):
        """Test generating policy with empty actions for a role"""
        rego = await policy_service.generate_service_policy(
            service_name="test_service",
            resource_type="test_resource",
            actions={"admin": ["test_action"], "viewer": []},  # Empty viewer actions
        )

        assert "package rbac" in rego
        assert "test_action" in rego
        # Should not generate role_check for viewer since it has no actions

    def test_get_policy_service_singleton(self):
        """Test that get_policy_service returns singleton"""
        with patch("app.services.policy_service.settings") as mock_settings:
            mock_settings.OPA_URL = "http://localhost:8181/v1/data/rbac/allow"

            service1 = get_policy_service()
            service2 = get_policy_service()

            assert service1 is service2
