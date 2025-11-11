"""
Unit tests for ApprovalsService

Tests the business logic of approval request operations with mocked database.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from workflow_core_sdk.services.approvals_service import ApprovalsService


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    return MagicMock()


@pytest.fixture
def sample_approval():
    """Sample approval request for testing"""
    approval_id = str(uuid.uuid4())
    execution_id = str(uuid.uuid4())
    return {
        "id": approval_id,
        "execution_id": execution_id,
        "step_id": "step-1",
        "status": "pending",
        "message": "Please approve this action",
        "requested_at": "2024-01-01T00:00:00Z",
        "requested_by": "user-123",
    }


class TestListApprovalRequests:
    """Tests for listing approval requests"""

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_list_approval_requests_no_filters(self, mock_db_class, mock_session, sample_approval):
        """Test listing all approval requests without filters"""
        mock_db = MagicMock()
        mock_db.list_approval_requests.return_value = [sample_approval]
        mock_db_class.return_value = mock_db

        approvals = ApprovalsService.list_approval_requests(mock_session, limit=100, offset=0)

        assert len(approvals) == 1
        assert approvals[0]["id"] == sample_approval["id"]
        mock_db.list_approval_requests.assert_called_once_with(
            mock_session, execution_id=None, status=None, limit=100, offset=0
        )

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_list_approval_requests_with_execution_id(self, mock_db_class, mock_session, sample_approval):
        """Test listing approval requests filtered by execution_id"""
        mock_db = MagicMock()
        mock_db.list_approval_requests.return_value = [sample_approval]
        mock_db_class.return_value = mock_db

        execution_id = sample_approval["execution_id"]
        approvals = ApprovalsService.list_approval_requests(
            mock_session, execution_id=execution_id, limit=100, offset=0
        )

        assert len(approvals) == 1
        assert approvals[0]["execution_id"] == execution_id
        mock_db.list_approval_requests.assert_called_once_with(
            mock_session, execution_id=execution_id, status=None, limit=100, offset=0
        )

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_list_approval_requests_with_status(self, mock_db_class, mock_session, sample_approval):
        """Test listing approval requests filtered by status"""
        mock_db = MagicMock()
        mock_db.list_approval_requests.return_value = [sample_approval]
        mock_db_class.return_value = mock_db

        approvals = ApprovalsService.list_approval_requests(mock_session, status="pending", limit=100, offset=0)

        assert len(approvals) == 1
        assert approvals[0]["status"] == "pending"
        mock_db.list_approval_requests.assert_called_once_with(
            mock_session, execution_id=None, status="pending", limit=100, offset=0
        )

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_list_approval_requests_with_all_filters(self, mock_db_class, mock_session, sample_approval):
        """Test listing approval requests with all filters"""
        mock_db = MagicMock()
        mock_db.list_approval_requests.return_value = [sample_approval]
        mock_db_class.return_value = mock_db

        execution_id = sample_approval["execution_id"]
        approvals = ApprovalsService.list_approval_requests(
            mock_session, execution_id=execution_id, status="pending", limit=50, offset=10
        )

        assert len(approvals) == 1
        mock_db.list_approval_requests.assert_called_once_with(
            mock_session, execution_id=execution_id, status="pending", limit=50, offset=10
        )

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_list_approval_requests_empty(self, mock_db_class, mock_session):
        """Test listing approval requests when none exist"""
        mock_db = MagicMock()
        mock_db.list_approval_requests.return_value = []
        mock_db_class.return_value = mock_db

        approvals = ApprovalsService.list_approval_requests(mock_session, limit=100, offset=0)

        assert len(approvals) == 0

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_list_approval_requests_with_pagination(self, mock_db_class, mock_session):
        """Test listing approval requests with pagination"""
        mock_db = MagicMock()
        mock_db.list_approval_requests.return_value = []
        mock_db_class.return_value = mock_db

        approvals = ApprovalsService.list_approval_requests(mock_session, limit=10, offset=20)

        assert len(approvals) == 0
        mock_db.list_approval_requests.assert_called_once_with(
            mock_session, execution_id=None, status=None, limit=10, offset=20
        )


class TestGetApprovalRequest:
    """Tests for getting a single approval request"""

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_get_approval_request_success(self, mock_db_class, mock_session, sample_approval):
        """Test getting an approval request by ID"""
        mock_db = MagicMock()
        mock_db.get_approval_request.return_value = sample_approval
        mock_db_class.return_value = mock_db

        approval = ApprovalsService.get_approval_request(mock_session, sample_approval["id"])

        assert approval is not None
        assert approval["id"] == sample_approval["id"]
        assert approval["status"] == "pending"
        mock_db.get_approval_request.assert_called_once_with(mock_session, sample_approval["id"])

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_get_approval_request_not_found(self, mock_db_class, mock_session):
        """Test getting a non-existent approval request"""
        mock_db = MagicMock()
        mock_db.get_approval_request.return_value = None
        mock_db_class.return_value = mock_db

        approval_id = str(uuid.uuid4())
        approval = ApprovalsService.get_approval_request(mock_session, approval_id)

        assert approval is None
        mock_db.get_approval_request.assert_called_once_with(mock_session, approval_id)


class TestCreateApprovalRequest:
    """Tests for creating approval requests"""

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_create_approval_request_success(self, mock_db_class, mock_session):
        """Test creating a new approval request"""
        mock_db = MagicMock()
        approval_id = str(uuid.uuid4())
        mock_db.create_approval_request.return_value = approval_id
        mock_db_class.return_value = mock_db

        data = {
            "execution_id": str(uuid.uuid4()),
            "step_id": "step-1",
            "message": "Please approve",
            "requested_by": "user-123",
        }

        result_id = ApprovalsService.create_approval_request(mock_session, data)

        assert result_id == approval_id
        mock_db.create_approval_request.assert_called_once_with(mock_session, data)

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_create_approval_request_with_all_fields(self, mock_db_class, mock_session):
        """Test creating an approval request with all fields"""
        mock_db = MagicMock()
        approval_id = str(uuid.uuid4())
        mock_db.create_approval_request.return_value = approval_id
        mock_db_class.return_value = mock_db

        data = {
            "execution_id": str(uuid.uuid4()),
            "step_id": "step-1",
            "status": "pending",
            "message": "Please approve this action",
            "requested_by": "user-123",
            "metadata": {"priority": "high"},
        }

        result_id = ApprovalsService.create_approval_request(mock_session, data)

        assert result_id == approval_id
        mock_db.create_approval_request.assert_called_once_with(mock_session, data)


class TestUpdateApprovalRequest:
    """Tests for updating approval requests"""

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_update_approval_request_success(self, mock_db_class, mock_session):
        """Test updating an approval request"""
        mock_db = MagicMock()
        mock_db.update_approval_request.return_value = True
        mock_db_class.return_value = mock_db

        approval_id = str(uuid.uuid4())
        changes = {"status": "approved", "approved_by": "user-456"}

        result = ApprovalsService.update_approval_request(mock_session, approval_id, changes)

        assert result is True
        mock_db.update_approval_request.assert_called_once_with(mock_session, approval_id, changes)

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_update_approval_request_not_found(self, mock_db_class, mock_session):
        """Test updating a non-existent approval request"""
        mock_db = MagicMock()
        mock_db.update_approval_request.return_value = False
        mock_db_class.return_value = mock_db

        approval_id = str(uuid.uuid4())
        changes = {"status": "approved"}

        result = ApprovalsService.update_approval_request(mock_session, approval_id, changes)

        assert result is False
        mock_db.update_approval_request.assert_called_once_with(mock_session, approval_id, changes)

    @patch("workflow_core_sdk.services.approvals_service.DatabaseService")
    def test_update_approval_request_reject(self, mock_db_class, mock_session):
        """Test rejecting an approval request"""
        mock_db = MagicMock()
        mock_db.update_approval_request.return_value = True
        mock_db_class.return_value = mock_db

        approval_id = str(uuid.uuid4())
        changes = {"status": "rejected", "rejected_by": "user-789", "rejection_reason": "Not authorized"}

        result = ApprovalsService.update_approval_request(mock_session, approval_id, changes)

        assert result is True
        mock_db.update_approval_request.assert_called_once_with(mock_session, approval_id, changes)

