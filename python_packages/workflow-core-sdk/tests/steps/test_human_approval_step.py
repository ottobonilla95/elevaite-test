"""
Unit tests for human_approval_step

Tests human approval workflow step with local and DBOS backends.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from workflow_core_sdk.steps.human_steps import human_approval_step
from workflow_core_sdk.execution_context import ExecutionContext, StepStatus, ExecutionStatus


@pytest.fixture
def execution_context():
    """Create a mock execution context"""
    context = MagicMock(spec=ExecutionContext)
    context.execution_id = "test-execution-id"
    context.workflow_id = "test-workflow-id"
    context.step_io_data = {}
    context.status = ExecutionStatus.RUNNING
    return context


@pytest.fixture
def step_config():
    """Basic step configuration"""
    return {
        "step_id": "approval-step-1",
        "step_type": "human_approval",
        "parameters": {
            "prompt": "Please approve this action",
            "timeout_seconds": 120,
            "approver_role": "admin",
            "require_comment": True,
        },
    }


class TestLocalBackendApproval:
    """Tests for human approval with local backend"""

    @pytest.mark.asyncio
    async def test_local_approval_waiting(self, step_config, execution_context):
        """Test that local backend returns WAITING status when no decision is injected"""
        result = await human_approval_step(step_config, {}, execution_context)

        assert result.status == StepStatus.WAITING
        assert result.output_data["prompt"] == "Please approve this action"
        assert execution_context.status == ExecutionStatus.WAITING

    @pytest.mark.asyncio
    async def test_local_approval_approved_via_injection(self, step_config, execution_context):
        """Test that local backend completes immediately when decision is injected"""
        # Inject approval decision
        execution_context.step_io_data["approval-step-1"] = {
            "decision": "approved",
            "decided_by": "admin@example.com",
            "comment": "Looks good!",
        }

        result = await human_approval_step(step_config, {}, execution_context)

        assert result.status == StepStatus.COMPLETED
        assert result.output_data["decision"] == "approved"
        assert result.output_data["decided_by"] == "admin@example.com"
        assert result.output_data["comment"] == "Looks good!"

    @pytest.mark.asyncio
    async def test_local_approval_denied_via_injection(self, step_config, execution_context):
        """Test that local backend completes with denied decision"""
        # Inject denial decision
        execution_context.step_io_data["approval-step-1"] = {
            "decision": "denied",
            "decided_by": "admin@example.com",
            "comment": "Not approved",
        }

        result = await human_approval_step(step_config, {}, execution_context)

        assert result.status == StepStatus.COMPLETED
        assert result.output_data["decision"] == "denied"


class TestApprovalMetadata:
    """Tests for approval metadata handling"""

    @pytest.mark.asyncio
    async def test_approval_with_all_metadata(self, step_config, execution_context):
        """Test that all metadata fields are properly included"""
        result = await human_approval_step(step_config, {}, execution_context)

        assert result.output_data["approval_metadata"]["approver_role"] == "admin"
        assert result.output_data["approval_metadata"]["require_comment"] is True
        assert result.output_data["approval_metadata"]["backend"] == "local"

    @pytest.mark.asyncio
    async def test_approval_with_minimal_config(self, execution_context):
        """Test approval with minimal configuration"""
        minimal_config = {
            "step_id": "approval-step-2",
            "step_type": "human_approval",
            "parameters": {"prompt": "Approve?"},
        }

        result = await human_approval_step(minimal_config, {}, execution_context)

        assert result.status == StepStatus.WAITING
        assert result.output_data["prompt"] == "Approve?"
        assert result.output_data["approval_metadata"]["approver_role"] is None
        assert result.output_data["approval_metadata"]["require_comment"] is None
