"""
Integration tests for Analytics API endpoints.

Tests all analytics operations including:
- Health check
- Agent usage statistics
- Tool usage statistics
- Workflow performance
- Error summary
- Session activity
- Analytics summary
- Execution details
- Session details

Note: Most analytics endpoints are currently stubs returning empty data.
These tests verify the API contract and response structure.
"""

from fastapi.testclient import TestClient


class TestAnalyticsAPI:
    """Test suite for Analytics API endpoints."""

    def test_analytics_health(self, test_client: TestClient):
        """Test analytics health check endpoint."""
        response = test_client.get("/api/analytics/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "analytics"
        assert "timestamp" in data
        assert "available_endpoints" in data
        assert isinstance(data["available_endpoints"], list)
        assert len(data["available_endpoints"]) > 0

    def test_get_agent_usage_statistics_no_params(self, test_client: TestClient):
        """Test getting agent usage statistics without parameters."""
        response = test_client.get("/api/analytics/agents/usage")

        assert response.status_code == 200
        data = response.json()
        # Currently returns empty list (stub)
        assert isinstance(data, list)

    def test_get_agent_usage_statistics_with_days(self, test_client: TestClient):
        """Test getting agent usage statistics with days parameter."""
        response = test_client.get("/api/analytics/agents/usage?days=7")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_agent_usage_statistics_with_date_range(self, test_client: TestClient):
        """Test getting agent usage statistics with date range."""
        response = test_client.get("/api/analytics/agents/usage?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_tool_usage_statistics_no_params(self, test_client: TestClient):
        """Test getting tool usage statistics without parameters."""
        response = test_client.get("/api/analytics/tools/usage")

        assert response.status_code == 200
        data = response.json()
        # Currently returns empty list (stub)
        assert isinstance(data, list)

    def test_get_tool_usage_statistics_with_days(self, test_client: TestClient):
        """Test getting tool usage statistics with days parameter."""
        response = test_client.get("/api/analytics/tools/usage?days=30")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_workflow_performance_no_params(self, test_client: TestClient):
        """Test getting workflow performance statistics without parameters."""
        response = test_client.get("/api/analytics/workflows/performance")

        assert response.status_code == 200
        data = response.json()
        # Currently returns empty list (stub)
        assert isinstance(data, list)

    def test_get_workflow_performance_with_days(self, test_client: TestClient):
        """Test getting workflow performance statistics with days parameter."""
        response = test_client.get("/api/analytics/workflows/performance?days=14")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_error_summary_no_params(self, test_client: TestClient):
        """Test getting error summary without parameters."""
        response = test_client.get("/api/analytics/errors/summary")

        assert response.status_code == 200
        data = response.json()
        # Currently returns empty list (stub)
        assert isinstance(data, list)

    def test_get_error_summary_with_days(self, test_client: TestClient):
        """Test getting error summary with days parameter."""
        response = test_client.get("/api/analytics/errors/summary?days=7")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_session_activity_no_params(self, test_client: TestClient):
        """Test getting session activity statistics without parameters."""
        response = test_client.get("/api/analytics/sessions/activity")

        assert response.status_code == 200
        data = response.json()
        # Currently returns empty dict (stub)
        assert isinstance(data, dict)

    def test_get_session_activity_with_days(self, test_client: TestClient):
        """Test getting session activity statistics with days parameter."""
        response = test_client.get("/api/analytics/sessions/activity?days=30")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_analytics_summary_default(self, test_client: TestClient):
        """Test getting analytics summary with default parameters."""
        response = test_client.get("/api/analytics/summary")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        # Verify expected structure
        assert "time_period" in data
        assert "agent_stats" in data
        assert "tool_stats" in data
        assert "workflow_stats" in data
        assert "error_summary" in data
        assert "session_stats" in data

        # Verify types (currently stubs)
        assert isinstance(data["agent_stats"], list)
        assert isinstance(data["tool_stats"], list)
        assert isinstance(data["workflow_stats"], list)
        assert isinstance(data["error_summary"], list)
        assert isinstance(data["session_stats"], dict)

    def test_get_analytics_summary_with_days(self, test_client: TestClient):
        """Test getting analytics summary with custom days parameter."""
        response = test_client.get("/api/analytics/summary?days=14")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "agent_stats" in data
        assert "time_period" in data

    def test_get_analytics_summary_with_date_range(self, test_client: TestClient):
        """Test getting analytics summary with date range."""
        response = test_client.get("/api/analytics/summary?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_execution_details_not_found(self, test_client: TestClient):
        """Test getting execution details for non-existent execution."""
        fake_id = "nonexistent-execution-12345"
        response = test_client.get(f"/api/analytics/executions/{fake_id}")

        # Currently stubbed to always return 404
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_session_details_not_found(self, test_client: TestClient):
        """Test getting session details for non-existent session."""
        fake_id = "nonexistent-session-12345"
        response = test_client.get(f"/api/analytics/sessions/{fake_id}")

        # Currently stubbed to always return 404
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_analytics_endpoints_accept_invalid_dates_gracefully(self, test_client: TestClient):
        """Test that analytics endpoints handle invalid dates gracefully."""
        # Invalid date format
        response = test_client.get("/api/analytics/agents/usage?start_date=invalid-date")

        # Should return 422 (validation error) or handle gracefully
        assert response.status_code in [200, 422]

    def test_analytics_summary_structure_consistency(self, test_client: TestClient):
        """Test that analytics summary always returns consistent structure."""
        # Call multiple times to ensure consistency
        for _ in range(3):
            response = test_client.get("/api/analytics/summary")
            assert response.status_code == 200
            data = response.json()

            # Verify all expected keys are present
            expected_keys = ["time_period", "agent_stats", "tool_stats", "workflow_stats", "error_summary", "session_stats"]
            for key in expected_keys:
                assert key in data, f"Missing key: {key}"
