"""
Tests for Approvals Router

Tests all approval endpoints:
- GET /approvals - List approval requests
- GET /approvals/{approval_id} - Get specific approval
- POST /approvals/{approval_id}/approve - Approve request
- POST /approvals/{approval_id}/deny - Deny request
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from workflow_core_sdk.db.models import ApprovalStatus


@pytest.fixture
def sample_approval_data():
    """Sample approval request data for testing"""
    workflow_id = str(uuid.uuid4())
    execution_id = str(uuid.uuid4())
    approval_id = str(uuid.uuid4())

    return {
        "id": approval_id,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "step_id": "approval_step_1",
        "status": ApprovalStatus.PENDING,
        "prompt": "Please approve this action",
        "approval_metadata": {
            "approver_role": "admin",
            "require_comment": True,
            "backend": "local",
        },
        "response_payload": None,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "decided_at": None,
        "decided_by": None,
    }


@pytest.fixture
def multiple_approvals(sample_approval_data):
    """Multiple approval requests for list testing"""
    approvals = []
    for i in range(3):
        approval = sample_approval_data.copy()
        approval["id"] = str(uuid.uuid4())
        approval["step_id"] = f"approval_step_{i}"
        if i == 1:
            approval["status"] = ApprovalStatus.APPROVED
            approval["decided_at"] = datetime.now(timezone.utc).isoformat()
            approval["decided_by"] = "user123"
        approvals.append(approval)
    return approvals


@pytest.mark.api
class TestListApprovals:
    """Tests for GET /approvals endpoint"""

    @pytest.mark.api
    def test_list_all_approvals(
        self, authenticated_client: TestClient, multiple_approvals
    ):
        """Test listing all approval requests"""
        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.list_approval_requests"
        ) as mock_list:
            mock_list.return_value = multiple_approvals

            response = authenticated_client.get("/approvals")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            assert all("id" in item for item in data)
            mock_list.assert_called_once()

    @pytest.mark.api
    def test_list_approvals_with_execution_id_filter(
        self, authenticated_client: TestClient, sample_approval_data
    ):
        """Test filtering approvals by execution_id"""
        execution_id = sample_approval_data["execution_id"]

        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.list_approval_requests"
        ) as mock_list:
            mock_list.return_value = [sample_approval_data]

            response = authenticated_client.get(
                f"/approvals?execution_id={execution_id}"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["execution_id"] == execution_id
            mock_list.assert_called_once()
            call_kwargs = mock_list.call_args[1]
            assert call_kwargs["execution_id"] == execution_id

    @pytest.mark.api
    def test_list_approvals_with_status_filter(
        self, authenticated_client: TestClient, multiple_approvals
    ):
        """Test filtering approvals by status"""
        approved_only = [
            a for a in multiple_approvals if a["status"] == ApprovalStatus.APPROVED
        ]

        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.list_approval_requests"
        ) as mock_list:
            mock_list.return_value = approved_only

            response = authenticated_client.get("/approvals?status=approved")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "approved"
            mock_list.assert_called_once()
            call_kwargs = mock_list.call_args[1]
            assert call_kwargs["status"] == "approved"

    @pytest.mark.api
    def test_list_approvals_with_pagination(
        self, authenticated_client: TestClient, multiple_approvals
    ):
        """Test pagination parameters"""
        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.list_approval_requests"
        ) as mock_list:
            mock_list.return_value = multiple_approvals[:2]

            response = authenticated_client.get("/approvals?limit=2&offset=0")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            mock_list.assert_called_once()
            call_kwargs = mock_list.call_args[1]
            assert call_kwargs["limit"] == 2
            assert call_kwargs["offset"] == 0

    @pytest.mark.api
    def test_list_approvals_empty_result(self, authenticated_client: TestClient):
        """Test listing when no approvals exist"""
        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.list_approval_requests"
        ) as mock_list:
            mock_list.return_value = []

            response = authenticated_client.get("/approvals")

            assert response.status_code == 200
            assert response.json() == []


@pytest.mark.api
class TestGetApproval:
    """Tests for GET /approvals/{approval_id} endpoint"""

    @pytest.mark.api
    def test_get_approval_success(
        self, authenticated_client: TestClient, sample_approval_data
    ):
        """Test getting a specific approval request"""
        approval_id = sample_approval_data["id"]

        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
        ) as mock_get:
            mock_get.return_value = sample_approval_data

            response = authenticated_client.get(f"/approvals/{approval_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == approval_id
            assert data["status"] == "pending"
            assert data["prompt"] == "Please approve this action"
            mock_get.assert_called_once_with(mock_get.call_args[0][0], approval_id)

    @pytest.mark.api
    def test_get_approval_not_found(self, authenticated_client: TestClient):
        """Test getting non-existent approval returns 404"""
        approval_id = str(uuid.uuid4())

        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
        ) as mock_get:
            mock_get.return_value = None

            response = authenticated_client.get(f"/approvals/{approval_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


@pytest.mark.api
class TestApproveRequest:
    """Tests for POST /approvals/{approval_id}/approve endpoint"""

    @pytest.mark.api
    def test_approve_request_success_local_backend(
        self, authenticated_client: TestClient, sample_approval_data
    ):
        """Test approving a request with local backend"""
        approval_id = sample_approval_data["id"]
        decision_body = {
            "payload": {"approved": True},
            "decided_by": "user123",
            "comment": "Looks good",
        }

        with (
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
            ) as mock_get,
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.update_approval_request"
            ) as mock_update,
            patch.object(
                authenticated_client.app.state.workflow_engine,
                "resume_execution",
                new_callable=AsyncMock,
            ) as mock_resume,
        ):
            mock_get.return_value = sample_approval_data
            mock_update.return_value = True

            response = authenticated_client.post(
                f"/approvals/{approval_id}/approve", json=decision_body
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["backend"] == "local"

            # Verify DB update was called
            mock_update.assert_called_once()
            update_call_args = mock_update.call_args[0]
            update_data = update_call_args[2]
            assert update_data["status"] == ApprovalStatus.APPROVED
            assert update_data["decided_by"] == "user123"

            # Verify workflow engine resume was called
            mock_resume.assert_called_once()

    @pytest.mark.api
    def test_approve_request_success_dbos_backend(
        self, authenticated_client: TestClient, sample_approval_data
    ):
        """Test approving a request with DBOS backend"""
        approval_id = sample_approval_data["id"]
        sample_approval_data["approval_metadata"]["backend"] = "dbos"
        decision_body = {
            "payload": {"approved": True},
            "decided_by": "user123",
        }

        with (
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
            ) as mock_get,
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.update_approval_request"
            ) as mock_update,
        ):
            mock_get.return_value = sample_approval_data
            mock_update.return_value = True

            response = authenticated_client.post(
                f"/approvals/{approval_id}/approve", json=decision_body
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["backend"] == "dbos"

            # Verify DB update was called
            mock_update.assert_called_once()

    @pytest.mark.api
    def test_approve_request_not_found(self, authenticated_client: TestClient):
        """Test approving non-existent request returns 404"""
        approval_id = str(uuid.uuid4())
        decision_body = {"decided_by": "user123"}

        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
        ) as mock_get:
            mock_get.return_value = None

            response = authenticated_client.post(
                f"/approvals/{approval_id}/approve", json=decision_body
            )

            assert response.status_code == 404

    @pytest.mark.api
    def test_approve_request_with_empty_payload(
        self, authenticated_client: TestClient, sample_approval_data
    ):
        """Test approving with minimal decision body"""
        approval_id = sample_approval_data["id"]

        with (
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
            ) as mock_get,
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.update_approval_request"
            ) as mock_update,
            patch.object(
                authenticated_client.app.state.workflow_engine,
                "resume_execution",
                new_callable=AsyncMock,
            ),
        ):
            mock_get.return_value = sample_approval_data
            mock_update.return_value = True

            response = authenticated_client.post(
                f"/approvals/{approval_id}/approve", json={}
            )

            assert response.status_code == 200


@pytest.mark.api
class TestDenyRequest:
    """Tests for POST /approvals/{approval_id}/deny endpoint"""

    @pytest.mark.api
    def test_deny_request_success_local_backend(
        self, authenticated_client: TestClient, sample_approval_data
    ):
        """Test denying a request with local backend"""
        approval_id = sample_approval_data["id"]
        decision_body = {
            "payload": {"reason": "Not authorized"},
            "decided_by": "user123",
            "comment": "Insufficient permissions",
        }

        with (
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
            ) as mock_get,
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.update_approval_request"
            ) as mock_update,
            patch.object(
                authenticated_client.app.state.workflow_engine,
                "resume_execution",
                new_callable=AsyncMock,
            ) as mock_resume,
        ):
            mock_get.return_value = sample_approval_data
            mock_update.return_value = True

            response = authenticated_client.post(
                f"/approvals/{approval_id}/deny", json=decision_body
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["backend"] == "local"

            # Verify DB update was called with DENIED status
            mock_update.assert_called_once()
            update_call_args = mock_update.call_args[0]
            update_data = update_call_args[2]
            assert update_data["status"] == ApprovalStatus.DENIED
            assert update_data["decided_by"] == "user123"

            # Verify workflow engine resume was called
            mock_resume.assert_called_once()

    @pytest.mark.api
    def test_deny_request_success_dbos_backend(
        self, authenticated_client: TestClient, sample_approval_data
    ):
        """Test denying a request with DBOS backend"""
        approval_id = sample_approval_data["id"]
        sample_approval_data["approval_metadata"]["backend"] = "dbos"
        decision_body = {"decided_by": "user123"}

        with (
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
            ) as mock_get,
            patch(
                "workflow_core_sdk.services.approvals_service.ApprovalsService.update_approval_request"
            ) as mock_update,
        ):
            mock_get.return_value = sample_approval_data
            mock_update.return_value = True

            response = authenticated_client.post(
                f"/approvals/{approval_id}/deny", json=decision_body
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["backend"] == "dbos"

    @pytest.mark.api
    def test_deny_request_not_found(self, authenticated_client: TestClient):
        """Test denying non-existent request returns 404"""
        approval_id = str(uuid.uuid4())
        decision_body = {"decided_by": "user123"}

        with patch(
            "workflow_core_sdk.services.approvals_service.ApprovalsService.get_approval_request"
        ) as mock_get:
            mock_get.return_value = None

            response = authenticated_client.post(
                f"/approvals/{approval_id}/deny", json=decision_body
            )

            assert response.status_code == 404
