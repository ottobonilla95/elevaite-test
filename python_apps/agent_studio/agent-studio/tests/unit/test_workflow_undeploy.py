import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.workflow_endpoints import (
    stop_workflow_deployment,
    delete_workflow_deployment_by_name,
)


@pytest.mark.unit
class TestWorkflowUndeployFunctionality:

    @patch("api.workflow_endpoints.crud")
    @patch("api.workflow_endpoints.workflow_service")
    def test_stop_workflow_deployment_success_development(
        self, mock_workflow_service, mock_crud
    ):
        mock_db = Mock(spec=Session)

        mock_deployment = Mock()
        mock_deployment.id = 1
        mock_deployment.name = "test-workflow"
        mock_deployment.environment = "development"
        mock_deployment.status = "active"

        mock_updated_deployment = Mock()
        mock_updated_deployment.deployment_id = 1
        mock_updated_deployment.status = "inactive"
        mock_updated_deployment.stopped_at = None

        mock_crud.get_workflow_deployment_by_name.return_value = mock_deployment
        mock_crud.update_workflow_deployment.return_value = mock_updated_deployment
        mock_workflow_service.ACTIVE_WORKFLOWS = {"test-workflow": Mock()}

        result = stop_workflow_deployment("test-workflow", mock_db)

        assert result["message"] == "Deployment 'test-workflow' stopped successfully"
        assert result["deployment_id"] == "1"
        assert result["status"] == "inactive"

        mock_crud.get_workflow_deployment_by_name.assert_called_with(
            mock_db, "test-workflow", "development"
        )
        mock_crud.update_workflow_deployment.assert_called_once()

        assert "test-workflow" not in mock_workflow_service.ACTIVE_WORKFLOWS

    @patch("api.workflow_endpoints.crud")
    @patch("api.workflow_endpoints.workflow_service")
    def test_stop_workflow_deployment_fallback_to_production(
        self, mock_workflow_service, mock_crud
    ):
        mock_db = Mock(spec=Session)

        mock_deployment = Mock()
        mock_deployment.id = 2
        mock_deployment.name = "prod-workflow"
        mock_deployment.environment = "production"
        mock_deployment.status = "active"

        mock_updated_deployment = Mock()
        mock_updated_deployment.deployment_id = 2
        mock_updated_deployment.status = "inactive"
        mock_updated_deployment.stopped_at = None

        mock_crud.get_workflow_deployment_by_name.side_effect = [None, mock_deployment]
        mock_crud.update_workflow_deployment.return_value = mock_updated_deployment
        mock_workflow_service.ACTIVE_WORKFLOWS = {"prod-workflow": Mock()}

        result = stop_workflow_deployment("prod-workflow", mock_db)

        assert result["message"] == "Deployment 'prod-workflow' stopped successfully"
        assert result["deployment_id"] == "2"

        assert mock_crud.get_workflow_deployment_by_name.call_count == 2
        mock_crud.get_workflow_deployment_by_name.assert_any_call(
            mock_db, "prod-workflow", "development"
        )
        mock_crud.get_workflow_deployment_by_name.assert_any_call(
            mock_db, "prod-workflow", "production"
        )

    @patch("api.workflow_endpoints.crud")
    def test_stop_workflow_deployment_not_found(self, mock_crud):
        mock_db = Mock(spec=Session)

        mock_crud.get_workflow_deployment_by_name.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            stop_workflow_deployment("nonexistent-workflow", mock_db)

        assert exc_info.value.status_code == 404
        assert "Workflow deployment 'nonexistent-workflow' not found" in str(
            exc_info.value.detail
        )

    @patch("api.workflow_endpoints.crud")
    def test_stop_workflow_deployment_already_inactive(self, mock_crud):
        mock_db = Mock(spec=Session)

        mock_deployment = Mock()
        mock_deployment.id = 1
        mock_deployment.name = "inactive-workflow"
        mock_deployment.environment = "development"
        mock_deployment.status = "inactive"

        mock_crud.get_workflow_deployment_by_name.return_value = mock_deployment

        with pytest.raises(HTTPException) as exc_info:
            stop_workflow_deployment("inactive-workflow", mock_db)

        assert exc_info.value.status_code == 400
        assert "already inactive" in str(exc_info.value.detail)

    @patch("api.workflow_endpoints.crud")
    @patch("api.workflow_endpoints.workflow_service")
    def test_delete_workflow_deployment_success(self, mock_workflow_service, mock_crud):
        mock_db = Mock(spec=Session)

        mock_deployment = Mock()
        mock_deployment.id = 1
        mock_deployment.name = "delete-workflow"
        mock_deployment.environment = "development"

        mock_crud.get_workflow_deployment_by_name.return_value = mock_deployment
        mock_crud.delete_workflow_deployment.return_value = True
        mock_workflow_service.ACTIVE_WORKFLOWS = {"delete-workflow": Mock()}

        result = delete_workflow_deployment_by_name("delete-workflow", mock_db)

        assert (
            result["message"]
            == "Workflow deployment 'delete-workflow' deleted successfully"
        )

        mock_crud.get_workflow_deployment_by_name.assert_called_with(
            mock_db, "delete-workflow", "development"
        )
        mock_crud.delete_workflow_deployment.assert_called_with(mock_db, 1)

        assert "delete-workflow" not in mock_workflow_service.ACTIVE_WORKFLOWS

    @patch("api.workflow_endpoints.crud")
    def test_delete_workflow_deployment_not_found(self, mock_crud):
        mock_db = Mock(spec=Session)

        mock_crud.get_workflow_deployment_by_name.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_workflow_deployment_by_name("nonexistent-workflow", mock_db)

        assert exc_info.value.status_code == 404
        assert "Workflow deployment 'nonexistent-workflow' not found" in str(
            exc_info.value.detail
        )

    @patch("api.workflow_endpoints.crud")
    @patch("api.workflow_endpoints.workflow_service")
    def test_stop_workflow_deployment_exception_handling(
        self, mock_workflow_service, mock_crud
    ):
        mock_db = Mock(spec=Session)

        mock_crud.get_workflow_deployment_by_name.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(HTTPException) as exc_info:
            stop_workflow_deployment("test-workflow", mock_db)

        assert exc_info.value.status_code == 500
        assert "Error stopping deployment" in str(exc_info.value.detail)

    @patch("api.workflow_endpoints.crud")
    @patch("api.workflow_endpoints.workflow_service")
    def test_delete_workflow_deployment_exception_handling(
        self, mock_workflow_service, mock_crud
    ):
        mock_db = Mock(spec=Session)

        mock_crud.get_workflow_deployment_by_name.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(HTTPException) as exc_info:
            delete_workflow_deployment_by_name("test-workflow", mock_db)

        assert exc_info.value.status_code == 500
        assert "Error deleting deployment" in str(exc_info.value.detail)

    @patch("api.workflow_endpoints.crud")
    @patch("api.workflow_endpoints.workflow_service")
    def test_memory_cleanup_on_stop(self, mock_workflow_service, mock_crud):
        mock_db = Mock(spec=Session)

        mock_deployment = Mock()
        mock_deployment.id = 1
        mock_deployment.name = "memory-test-workflow"
        mock_deployment.environment = "development"
        mock_deployment.status = "active"

        mock_crud.get_workflow_deployment_by_name.return_value = mock_deployment
        mock_crud.update_workflow_deployment_status.return_value = mock_deployment

        mock_workflow_service.ACTIVE_WORKFLOWS = {
            "memory-test-workflow": Mock(),
            "other-workflow": Mock(),
        }

        stop_workflow_deployment("memory-test-workflow", mock_db)

        assert "memory-test-workflow" not in mock_workflow_service.ACTIVE_WORKFLOWS
        assert "other-workflow" in mock_workflow_service.ACTIVE_WORKFLOWS

    @patch("api.workflow_endpoints.crud")
    @patch("api.workflow_endpoints.workflow_service")
    def test_memory_cleanup_on_delete(self, mock_workflow_service, mock_crud):
        mock_db = Mock(spec=Session)

        mock_deployment = Mock()
        mock_deployment.id = 1
        mock_deployment.name = "delete-memory-test"
        mock_deployment.environment = "development"

        mock_crud.get_workflow_deployment_by_name.return_value = mock_deployment
        mock_crud.delete_workflow_deployment.return_value = True

        mock_workflow_service.ACTIVE_WORKFLOWS = {
            "delete-memory-test": Mock(),
            "other-workflow": Mock(),
        }

        delete_workflow_deployment_by_name("delete-memory-test", mock_db)

        assert "delete-memory-test" not in mock_workflow_service.ACTIVE_WORKFLOWS
        assert "other-workflow" in mock_workflow_service.ACTIVE_WORKFLOWS
