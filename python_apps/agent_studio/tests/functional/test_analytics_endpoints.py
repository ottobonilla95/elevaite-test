import pytest


class TestAnalyticsEndpoints:
    def test_health_endpoint(self, test_client):
        response = test_client.get("/api/analytics/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "analytics"
        assert "timestamp" in data
        assert "available_endpoints" in data
        assert len(data["available_endpoints"]) >= 8

    def test_agents_usage_endpoint(self, test_client):
        response = test_client.get("/api/analytics/agents/usage")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_agents_usage_with_params(self, test_client):
        response = test_client.get("/api/analytics/agents/usage?days=7")
        assert response.status_code == 200

        response = test_client.get(
            "/api/analytics/agents/usage?start_date=2025-05-01&end_date=2025-05-29"
        )
        assert response.status_code == 200

    def test_tools_usage_endpoint(self, test_client):
        response = test_client.get("/api/analytics/tools/usage")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_workflows_performance_endpoint(self, test_client):
        response = test_client.get("/api/analytics/workflows/performance")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_errors_summary_endpoint(self, test_client):
        response = test_client.get("/api/analytics/errors/summary")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_sessions_activity_endpoint(self, test_client):
        response = test_client.get("/api/analytics/sessions/activity")
        assert response.status_code == 200

        data = response.json()
        assert "total_sessions" in data
        assert "active_sessions" in data
        assert "total_queries" in data
        assert "query_success_rate" in data

    def test_summary_endpoint(self, test_client):
        response = test_client.get("/api/analytics/summary")
        assert response.status_code == 200

        data = response.json()
        assert "time_period" in data
        assert "agent_stats" in data
        assert "tool_stats" in data
        assert "workflow_stats" in data
        assert "error_summary" in data
        assert "session_stats" in data


class TestAnalyticsIntegration:
    def test_analytics_with_sample_data(self, test_client):
        endpoints = [
            "/api/analytics/agents/usage",
            "/api/analytics/tools/usage",
            "/api/analytics/workflows/performance",
            "/api/analytics/errors/summary",
            "/api/analytics/sessions/activity",
            "/api/analytics/summary",
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200

            data = response.json()
            if endpoint == "/api/analytics/sessions/activity":
                assert isinstance(data, dict)
            elif endpoint == "/api/analytics/summary":
                assert isinstance(data, dict)
                assert "agent_stats" in data
            else:
                assert isinstance(data, list)

    def test_date_filtering(self, test_client):
        test_cases = [
            {"days": 1},
            {"days": 7},
            {"days": 30},
            {"start_date": "2025-05-01", "end_date": "2025-05-29"},
        ]

        for params in test_cases:
            response = test_client.get("/api/analytics/agents/usage", params=params)
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
