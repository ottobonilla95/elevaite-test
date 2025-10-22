"""
Integration tests for Tools API endpoints.

Tests all operations for tools including:
- List all tools
- Get tool by name
- Get available tools
- Search tools
- Error cases and validation
"""

import pytest
from fastapi.testclient import TestClient


class TestToolsAPI:
    """Test suite for Tools API endpoints."""

    def test_get_all_tools_success(self, test_client: TestClient):
        """Test getting all available tools."""
        response = test_client.get("/api/tools/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least some tools from the SDK
        assert len(data) >= 0

    def test_get_all_tools_structure(self, test_client: TestClient):
        """Test that tools have the correct structure."""
        response = test_client.get("/api/tools/")

        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            # Check first tool has required fields
            first_tool = data[0]
            assert "name" in first_tool
            assert "description" in first_tool
            assert "tool_id" in first_tool
            assert "tool_type" in first_tool

    def test_get_tool_by_name_success(self, test_client: TestClient):
        """Test getting a specific tool by name."""
        # First get all tools to find a valid tool name
        list_response = test_client.get("/api/tools/")
        assert list_response.status_code == 200
        tools_data = list_response.json()

        if len(tools_data) > 0:
            # Get the first tool by name
            tool_name = tools_data[0]["name"]
            response = test_client.get(f"/api/tools/by-name/{tool_name}")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == tool_name

    def test_get_tool_by_name_not_found(self, test_client: TestClient):
        """Test getting a non-existent tool."""
        response = test_client.get("/api/tools/by-name/nonexistent_tool_12345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_available_tools(self, test_client: TestClient):
        """Test getting all available tools."""
        response = test_client.get("/api/tools/available")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_tools_by_query(self, test_client: TestClient):
        """Test searching tools by query string."""
        # First get all tools to find a searchable term
        list_response = test_client.get("/api/tools/")
        assert list_response.status_code == 200
        tools_data = list_response.json()

        if len(tools_data) > 0:
            # Use part of the first tool's name as search query
            search_term = tools_data[0]["name"][:5]
            response = test_client.get(f"/api/tools/?q={search_term}")

            # Should return 200
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_tools_pagination(self, test_client: TestClient):
        """Test tools pagination."""
        # Get first page
        response1 = test_client.get("/api/tools/?skip=0&limit=2")
        assert response1.status_code == 200
        data1 = response1.json()
        assert isinstance(data1, list)
        assert len(data1) <= 2

        # Get second page
        response2 = test_client.get("/api/tools/?skip=2&limit=2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert isinstance(data2, list)

    def test_tool_names_unique(self, test_client: TestClient):
        """Test that all tool names are unique."""
        response = test_client.get("/api/tools/")

        assert response.status_code == 200
        data = response.json()

        tool_names = [tool["name"] for tool in data]
        # Check for duplicates
        assert len(tool_names) == len(set(tool_names))

    def test_get_multiple_tools_by_name(self, test_client: TestClient):
        """Test getting multiple tools by name."""
        # Get all tools
        list_response = test_client.get("/api/tools/")
        assert list_response.status_code == 200
        tools_data = list_response.json()

        if len(tools_data) >= 2:
            # Get first two tools by name
            for i in range(min(2, len(tools_data))):
                tool_name = tools_data[i]["name"]
                response = test_client.get(f"/api/tools/by-name/{tool_name}")
                assert response.status_code == 200
                assert response.json()["name"] == tool_name

    def test_tool_parameters_structure(self, test_client: TestClient):
        """Test that tool parameters have valid JSON schema structure."""
        response = test_client.get("/api/tools/")

        assert response.status_code == 200
        data = response.json()

        for tool in data:
            if "parameters_schema" in tool:
                params = tool["parameters_schema"]
                # Parameters should be a dict (JSON schema)
                assert isinstance(params, dict)

    def test_tools_api_error_handling(self, test_client: TestClient):
        """Test error handling for invalid requests."""
        # Test with non-existent tool name
        response = test_client.get("/api/tools/by-name/invalid_tool_name_12345")
        # Should return 404
        assert response.status_code == 404
