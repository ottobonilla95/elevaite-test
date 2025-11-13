"""
Tests for Monitoring Router

Tests all monitoring, metrics, and analytics endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from workflow_engine_poc.main import app

client = TestClient(app)


# ========== Metrics Tests ==========


class TestGetMetrics:
    """Tests for GET /metrics"""

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_metrics")
    def test_get_metrics_success(self, mock_get_metrics):
        """Test getting Prometheus metrics"""
        mock_metrics_data = """# HELP workflow_executions_total Total number of workflow executions
# TYPE workflow_executions_total counter
workflow_executions_total 42
# HELP workflow_execution_duration_seconds Workflow execution duration
# TYPE workflow_execution_duration_seconds histogram
workflow_execution_duration_seconds_bucket{le="1.0"} 10
workflow_execution_duration_seconds_bucket{le="5.0"} 25
workflow_execution_duration_seconds_bucket{le="+Inf"} 42
workflow_execution_duration_seconds_sum 150.5
workflow_execution_duration_seconds_count 42
"""
        mock_get_metrics.return_value = mock_metrics_data

        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "workflow_executions_total 42" in response.text
        assert "workflow_execution_duration_seconds" in response.text

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_metrics")
    def test_get_metrics_error(self, mock_get_metrics):
        """Test metrics endpoint error handling"""
        mock_get_metrics.side_effect = Exception("Metrics collection failed")

        response = client.get("/metrics")

        assert response.status_code == 500
        assert "Metrics collection failed" in response.json()["detail"]


# ========== Traces Tests ==========


class TestGetTraces:
    """Tests for GET /monitoring/traces"""

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_traces")
    def test_get_traces_success(self, mock_get_traces):
        """Test getting trace data"""
        mock_traces = [
            {
                "trace_id": "trace-1",
                "span_id": "span-1",
                "operation": "workflow.execute",
                "duration_ms": 150,
                "status": "success",
            },
            {
                "trace_id": "trace-2",
                "span_id": "span-2",
                "operation": "step.execute",
                "duration_ms": 50,
                "status": "success",
            },
        ]
        mock_get_traces.return_value = mock_traces

        response = client.get("/monitoring/traces")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["limit"] == 100
        assert len(data["traces"]) == 2
        assert data["traces"][0]["trace_id"] == "trace-1"

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_traces")
    def test_get_traces_with_limit(self, mock_get_traces):
        """Test getting traces with custom limit"""
        # Create 150 mock traces
        mock_traces = [{"trace_id": f"trace-{i}", "operation": "test"} for i in range(150)]
        mock_get_traces.return_value = mock_traces

        response = client.get("/monitoring/traces?limit=50")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 150
        assert data["limit"] == 50
        # Should return last 50 traces
        assert len(data["traces"]) == 50
        assert data["traces"][0]["trace_id"] == "trace-100"  # Last 50 start at index 100

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_traces")
    def test_get_traces_empty(self, mock_get_traces):
        """Test getting traces when none exist"""
        mock_get_traces.return_value = []

        response = client.get("/monitoring/traces")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["traces"]) == 0

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_traces")
    def test_get_traces_error(self, mock_get_traces):
        """Test traces endpoint error handling"""
        mock_get_traces.side_effect = Exception("Trace collection failed")

        response = client.get("/monitoring/traces")

        assert response.status_code == 500
        assert "Trace collection failed" in response.json()["detail"]


# ========== Monitoring Summary Tests ==========


class TestGetMonitoringSummary:
    """Tests for GET /monitoring/summary"""

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_monitoring_summary")
    def test_get_summary_success(self, mock_get_summary):
        """Test getting monitoring summary"""
        mock_summary = {
            "total_traces": 1000,
            "total_errors": 5,
            "avg_response_time_ms": 125.5,
            "uptime_seconds": 86400,
        }
        mock_get_summary.return_value = mock_summary

        response = client.get("/monitoring/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["monitoring_status"] == "active"
        assert data["summary"]["total_traces"] == 1000
        assert data["summary"]["total_errors"] == 5
        assert data["components"]["traces"] == "active"
        assert data["components"]["metrics"] == "active"
        assert data["components"]["error_tracking"] == "active"

    @patch("workflow_engine_poc.routers.monitoring.monitoring.get_monitoring_summary")
    def test_get_summary_error(self, mock_get_summary):
        """Test summary endpoint error handling"""
        mock_get_summary.side_effect = Exception("Summary generation failed")

        response = client.get("/monitoring/summary")

        assert response.status_code == 500
        assert "Summary generation failed" in response.json()["detail"]


# ========== Execution Analytics Tests ==========


class TestGetExecutionAnalytics:
    """Tests for GET /analytics/executions"""

    @patch("workflow_engine_poc.routers.monitoring.Request")
    def test_get_execution_analytics_success(self, mock_request_class):
        """Test getting execution analytics"""
        # Mock workflow engine
        mock_engine = AsyncMock()
        mock_execution_1 = MagicMock()
        mock_execution_1.get_status_summary.return_value = {
            "execution_id": "exec-1",
            "workflow_id": "wf-1",
            "status": "completed",
            "duration_ms": 1500,
        }
        mock_execution_2 = MagicMock()
        mock_execution_2.get_status_summary.return_value = {
            "execution_id": "exec-2",
            "workflow_id": "wf-2",
            "status": "running",
            "duration_ms": None,
        }
        mock_engine.get_execution_history = AsyncMock(return_value=[mock_execution_1, mock_execution_2])

        # Mock request with app state
        mock_request = MagicMock()
        mock_request.app.state.workflow_engine = mock_engine

        # Patch the request parameter
        with patch("workflow_engine_poc.routers.monitoring.Request", return_value=mock_request):
            # Need to inject the mock request into the endpoint
            # This is tricky with TestClient, so let's call the endpoint directly
            from workflow_engine_poc.routers.monitoring import get_execution_analytics
            import asyncio

            result = asyncio.run(get_execution_analytics(limit=100, offset=0, status=None, request=mock_request))

        assert result["total"] == 2
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert len(result["executions"]) == 2
        assert result["executions"][0]["execution_id"] == "exec-1"

    @patch("workflow_engine_poc.routers.monitoring.Request")
    def test_get_execution_analytics_with_filters(self, mock_request_class):
        """Test getting execution analytics with status filter"""
        mock_engine = AsyncMock()
        mock_execution = MagicMock()
        mock_execution.get_status_summary.return_value = {
            "execution_id": "exec-1",
            "status": "completed",
        }
        mock_engine.get_execution_history = AsyncMock(return_value=[mock_execution])

        mock_request = MagicMock()
        mock_request.app.state.workflow_engine = mock_engine

        from workflow_engine_poc.routers.monitoring import get_execution_analytics
        import asyncio

        result = asyncio.run(
            get_execution_analytics(limit=50, offset=10, status="completed", request=mock_request)
        )

        assert result["limit"] == 50
        assert result["offset"] == 10
        assert result["filter"]["status"] == "completed"
        # Verify the engine was called with correct parameters
        mock_engine.get_execution_history.assert_called_once_with(limit=50, offset=10, status="completed")


# ========== Error Analytics Tests ==========


class TestGetErrorAnalytics:
    """Tests for GET /analytics/errors"""

    @patch("workflow_engine_poc.routers.monitoring.error_handler.get_error_statistics")
    def test_get_error_analytics_all(self, mock_get_stats):
        """Test getting all error analytics"""
        mock_stats = {
            "total_errors": 10,
            "errors_by_type": {"ValueError": 5, "TypeError": 3, "RuntimeError": 2},
            "errors_by_component": {
                "workflow_engine": [{"error": "Error 1", "timestamp": "2024-01-01T00:00:00Z"}],
                "step_executor": [{"error": "Error 2", "timestamp": "2024-01-01T00:01:00Z"}],
            },
        }
        mock_get_stats.return_value = mock_stats

        response = client.get("/analytics/errors")

        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 10
        assert data["errors_by_type"]["ValueError"] == 5
        assert "workflow_engine" in data["errors_by_component"]

    @patch("workflow_engine_poc.routers.monitoring.error_handler.get_error_statistics")
    def test_get_error_analytics_by_component(self, mock_get_stats):
        """Test getting error analytics for specific component"""
        mock_stats = {
            "errors_by_component": {
                "workflow_engine": [
                    {"error": "Error 1", "timestamp": "2024-01-01T00:00:00Z"},
                    {"error": "Error 2", "timestamp": "2024-01-01T00:01:00Z"},
                ],
            },
        }
        mock_get_stats.return_value = mock_stats

        response = client.get("/analytics/errors?component=workflow_engine")

        assert response.status_code == 200
        data = response.json()
        assert data["component"] == "workflow_engine"
        assert data["total"] == 2
        assert len(data["errors"]) == 2
        assert data["errors"][0]["error"] == "Error 1"

    @patch("workflow_engine_poc.routers.monitoring.error_handler.get_error_statistics")
    def test_get_error_analytics_component_not_found(self, mock_get_stats):
        """Test getting error analytics for non-existent component"""
        mock_stats = {"errors_by_component": {}}
        mock_get_stats.return_value = mock_stats

        response = client.get("/analytics/errors?component=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["component"] == "nonexistent"
        assert data["total"] == 0
        assert data["errors"] == []

    @patch("workflow_engine_poc.routers.monitoring.error_handler.get_error_statistics")
    def test_get_error_analytics_error(self, mock_get_stats):
        """Test error analytics endpoint error handling"""
        mock_get_stats.side_effect = Exception("Error stats collection failed")

        response = client.get("/analytics/errors")

        assert response.status_code == 500
        assert "Error stats collection failed" in response.json()["detail"]

