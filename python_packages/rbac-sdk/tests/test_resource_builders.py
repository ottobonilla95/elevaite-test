"""
Brutal unit tests for resource builders in rbac_sdk.fastapi_helpers.

These tests cover:
- Project resource building
- Account resource building
- Organization resource building
- Missing headers
- Edge cases and security concerns
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from rbac_sdk.fastapi_helpers import (
    resource_builders,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)


class TestProjectFromHeaders:
    """Test project_from_headers resource builder."""

    def test_project_from_headers_all_present(self, mock_request_with_project_headers):
        """Test that all headers are extracted correctly."""
        builder = resource_builders.project_from_headers()
        resource = builder(mock_request_with_project_headers)

        assert resource["type"] == "project"
        assert resource["id"] == "proj-101"
        assert resource["organization_id"] == "org-456"
        assert resource["account_id"] == "acc-789"

    def test_project_from_headers_missing_project_id(self):
        """Test that missing project ID raises 400."""
        request = Mock()
        request.headers = {
            HDR_ORG_ID: "org-456",
            HDR_ACCOUNT_ID: "acc-789",
        }

        builder = resource_builders.project_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400
        assert HDR_PROJECT_ID in str(exc_info.value.detail)

    def test_project_from_headers_missing_org_id(self):
        """Test that missing org ID raises 400."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-101",
            HDR_ACCOUNT_ID: "acc-789",
        }

        builder = resource_builders.project_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400
        assert HDR_ORG_ID in str(exc_info.value.detail)

    def test_project_from_headers_missing_account_id(self):
        """Test that missing account ID is optional (not required)."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-101",
            HDR_ORG_ID: "org-456",
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        assert resource["type"] == "project"
        assert resource["id"] == "proj-101"
        assert resource["organization_id"] == "org-456"
        # account_id should not be in resource when not provided
        assert "account_id" not in resource

    def test_project_from_headers_custom_header_names(self):
        """Test that custom header names work."""
        request = Mock()
        request.headers = {
            "X-Custom-Project": "proj-999",
            "X-Custom-Org": "org-888",
            "X-Custom-Account": "acc-777",
        }

        builder = resource_builders.project_from_headers(
            project_header="X-Custom-Project",
            org_header="X-Custom-Org",
            account_header="X-Custom-Account",
        )
        resource = builder(request)

        assert resource["id"] == "proj-999"
        assert resource["organization_id"] == "org-888"
        assert resource["account_id"] == "acc-777"

    def test_project_from_headers_empty_project_id(self):
        """Test that empty project ID string raises 400."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "",
            HDR_ORG_ID: "org-456",
        }

        builder = resource_builders.project_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400

    def test_project_from_headers_empty_org_id(self):
        """Test that empty org ID string raises 400."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-101",
            HDR_ORG_ID: "",
        }

        builder = resource_builders.project_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400

    def test_project_from_headers_empty_account_id(self):
        """Test that empty account ID is treated as missing (optional)."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-101",
            HDR_ORG_ID: "org-456",
            HDR_ACCOUNT_ID: "",
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        # Empty string is falsy, should not be included
        assert "account_id" not in resource


class TestAccountFromHeaders:
    """Test account_from_headers resource builder."""

    def test_account_from_headers_all_present(self):
        """Test that all headers are extracted correctly."""
        request = Mock()
        request.headers = {
            HDR_ACCOUNT_ID: "acc-789",
            HDR_ORG_ID: "org-456",
        }

        builder = resource_builders.account_from_headers()
        resource = builder(request)

        assert resource["type"] == "account"
        assert resource["id"] == "acc-789"
        assert resource["organization_id"] == "org-456"
        assert resource["account_id"] == "acc-789"  # Duplicated for rego compatibility

    def test_account_from_headers_missing_account_id(self):
        """Test that missing account ID raises 400."""
        request = Mock()
        request.headers = {HDR_ORG_ID: "org-456"}

        builder = resource_builders.account_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400
        assert HDR_ACCOUNT_ID in str(exc_info.value.detail)

    def test_account_from_headers_missing_org_id(self):
        """Test that missing org ID raises 400."""
        request = Mock()
        request.headers = {HDR_ACCOUNT_ID: "acc-789"}

        builder = resource_builders.account_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400
        assert HDR_ORG_ID in str(exc_info.value.detail)

    def test_account_from_headers_custom_header_names(self):
        """Test that custom header names work."""
        request = Mock()
        request.headers = {
            "X-Custom-Account": "acc-999",
            "X-Custom-Org": "org-888",
        }

        builder = resource_builders.account_from_headers(
            account_header="X-Custom-Account",
            org_header="X-Custom-Org",
        )
        resource = builder(request)

        assert resource["id"] == "acc-999"
        assert resource["organization_id"] == "org-888"
        assert resource["account_id"] == "acc-999"

    def test_account_from_headers_empty_account_id(self):
        """Test that empty account ID raises 400."""
        request = Mock()
        request.headers = {
            HDR_ACCOUNT_ID: "",
            HDR_ORG_ID: "org-456",
        }

        builder = resource_builders.account_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400


class TestOrganizationFromHeaders:
    """Test organization_from_headers resource builder."""

    def test_organization_from_headers_present(self):
        """Test that org header is extracted correctly."""
        request = Mock()
        request.headers = {HDR_ORG_ID: "org-456"}

        builder = resource_builders.organization_from_headers()
        resource = builder(request)

        assert resource["type"] == "organization"
        assert resource["id"] == "org-456"
        assert resource["organization_id"] == "org-456"  # Duplicated for consistency

    def test_organization_from_headers_missing(self):
        """Test that missing org ID raises 400."""
        request = Mock()
        request.headers = {}

        builder = resource_builders.organization_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400
        assert HDR_ORG_ID in str(exc_info.value.detail)

    def test_organization_from_headers_custom_header_name(self):
        """Test that custom header name works."""
        request = Mock()
        request.headers = {"X-Custom-Org": "org-999"}

        builder = resource_builders.organization_from_headers(org_header="X-Custom-Org")
        resource = builder(request)

        assert resource["id"] == "org-999"
        assert resource["organization_id"] == "org-999"

    def test_organization_from_headers_empty(self):
        """Test that empty org ID raises 400."""
        request = Mock()
        request.headers = {HDR_ORG_ID: ""}

        builder = resource_builders.organization_from_headers()

        with pytest.raises(HTTPException) as exc_info:
            builder(request)

        assert exc_info.value.status_code == 400


class TestResourceBuilderSecurityEdgeCases:
    """Test security-critical edge cases in resource building."""

    def test_sql_injection_in_project_id(self):
        """Test that SQL injection attempts are passed through (validation is server-side)."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-123; DROP TABLE projects;--",
            HDR_ORG_ID: "org-456",
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        # Should pass through - server should validate/sanitize
        assert resource["id"] == "proj-123; DROP TABLE projects;--"

    def test_path_traversal_in_org_id(self):
        """Test that path traversal attempts are passed through."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-123",
            HDR_ORG_ID: "../../etc/passwd",
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        assert resource["organization_id"] == "../../etc/passwd"

    def test_very_long_ids(self):
        """Test that very long IDs are handled."""
        request = Mock()
        long_id = "a" * 10000
        request.headers = {
            HDR_PROJECT_ID: long_id,
            HDR_ORG_ID: long_id,
            HDR_ACCOUNT_ID: long_id,
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        assert resource["id"] == long_id
        assert resource["organization_id"] == long_id
        assert resource["account_id"] == long_id

    def test_unicode_in_ids(self):
        """Test that Unicode characters in IDs are handled."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "项目-123",
            HDR_ORG_ID: "组织-456",
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        assert resource["id"] == "项目-123"
        assert resource["organization_id"] == "组织-456"

    def test_special_characters_in_ids(self):
        """Test that special characters in IDs are handled."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-123!@#$%^&*()",
            HDR_ORG_ID: 'org-456<>?:"{}|',
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        assert resource["id"] == "proj-123!@#$%^&*()"
        assert resource["organization_id"] == 'org-456<>?:"{}|'

    def test_null_bytes_in_ids(self):
        """Test that null bytes in IDs are handled."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj\x00123",
            HDR_ORG_ID: "org\x00456",
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        assert resource["id"] == "proj\x00123"
        assert resource["organization_id"] == "org\x00456"

    def test_whitespace_only_ids(self):
        """Test that whitespace-only IDs are treated as truthy (passed through)."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "   ",
            HDR_ORG_ID: "\t\n",
        }

        builder = resource_builders.project_from_headers()
        resource = builder(request)

        # Whitespace strings are truthy in Python
        assert resource["id"] == "   "
        assert resource["organization_id"] == "\t\n"


class TestResourceBuilderConsistency:
    """Test consistency across different resource builders."""

    def test_all_builders_return_type_field(self):
        """Test that all builders include 'type' field."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-123",
            HDR_ACCOUNT_ID: "acc-456",
            HDR_ORG_ID: "org-789",
        }

        project_resource = resource_builders.project_from_headers()(request)
        account_resource = resource_builders.account_from_headers()(request)
        org_resource = resource_builders.organization_from_headers()(request)

        assert "type" in project_resource
        assert "type" in account_resource
        assert "type" in org_resource

    def test_all_builders_return_id_field(self):
        """Test that all builders include 'id' field."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-123",
            HDR_ACCOUNT_ID: "acc-456",
            HDR_ORG_ID: "org-789",
        }

        project_resource = resource_builders.project_from_headers()(request)
        account_resource = resource_builders.account_from_headers()(request)
        org_resource = resource_builders.organization_from_headers()(request)

        assert "id" in project_resource
        assert "id" in account_resource
        assert "id" in org_resource

    def test_all_builders_return_organization_id_field(self):
        """Test that all builders include 'organization_id' field."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-123",
            HDR_ACCOUNT_ID: "acc-456",
            HDR_ORG_ID: "org-789",
        }

        project_resource = resource_builders.project_from_headers()(request)
        account_resource = resource_builders.account_from_headers()(request)
        org_resource = resource_builders.organization_from_headers()(request)

        assert "organization_id" in project_resource
        assert "organization_id" in account_resource
        assert "organization_id" in org_resource

    def test_resource_types_are_correct(self):
        """Test that resource types match expected values."""
        request = Mock()
        request.headers = {
            HDR_PROJECT_ID: "proj-123",
            HDR_ACCOUNT_ID: "acc-456",
            HDR_ORG_ID: "org-789",
        }

        project_resource = resource_builders.project_from_headers()(request)
        account_resource = resource_builders.account_from_headers()(request)
        org_resource = resource_builders.organization_from_headers()(request)

        assert project_resource["type"] == "project"
        assert account_resource["type"] == "account"
        assert org_resource["type"] == "organization"
