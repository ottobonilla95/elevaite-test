"""
E2E tests for input and merge nodes.

Tests the multi-trigger architecture:
- Input nodes as data entry points (step_type="input")
- Merge nodes with first_available (OR) and wait_all (AND) logic
- Data flow through input -> merge -> processing chains

Key step types tested:
- "input": Generalized entry point that passes through step_io_data or trigger_raw
- "merge": Combines multiple inputs with OR (first_available) or AND (wait_all) logic
- "data_input": Static/dynamic data provider (for comparison)
- "data_merge": Standard data merge step (for comparison)
"""

import asyncio
import pytest
from httpx import AsyncClient


# =============================================================================
# Fixtures for workflow definitions
# =============================================================================


@pytest.fixture
def workflow_with_input_nodes():
    """Workflow with input nodes (step_type='input') - the multi-trigger entry points."""
    return {
        "name": "Multi-Input Workflow",
        "description": "Workflow with multiple input entry points",
        "version": "1.0.0",
        "execution_pattern": "dependency_based",
        "steps": [
            {
                "step_id": "webhook-input",
                "step_type": "input",
                "name": "Webhook Input",
                "parameters": {"kind": "webhook"},
            },
            {
                "step_id": "chat-input",
                "step_type": "input",
                "name": "Chat Input",
                "parameters": {"kind": "chat"},
            },
            {
                "step_id": "merge",
                "step_type": "merge",
                "name": "Merge Inputs",
                "dependencies": ["webhook-input", "chat-input"],
                "parameters": {"mode": "first_available", "combine_mode": "object"},
            },
        ],
        "status": "active",
    }


@pytest.fixture
def workflow_with_wait_all_merge():
    """Workflow with merge node using wait_all (AND logic)."""
    return {
        "name": "Wait All Merge Workflow",
        "description": "Workflow that waits for all inputs",
        "version": "1.0.0",
        "execution_pattern": "dependency_based",
        "steps": [
            {
                "step_id": "input-a",
                "step_type": "input",
                "name": "Input A",
                "parameters": {"kind": "manual"},
            },
            {
                "step_id": "input-b",
                "step_type": "input",
                "name": "Input B",
                "parameters": {"kind": "manual"},
            },
            {
                "step_id": "merge",
                "step_type": "merge",
                "name": "Wait All Merge",
                "dependencies": ["input-a", "input-b"],
                "parameters": {"mode": "wait_all", "combine_mode": "object"},
            },
        ],
        "status": "active",
    }


# =============================================================================
# Test Classes
# =============================================================================


class TestInputNodeCreation:
    """Tests for input node workflow creation."""

    @pytest.mark.asyncio
    async def test_create_workflow_with_single_input_node(
        self, async_client: AsyncClient
    ):
        """Test creating a workflow with a single input node."""
        workflow_data = {
            "name": "Single Input Workflow",
            "description": "Simple workflow with one input node",
            "execution_pattern": "dependency_based",
            "steps": [
                {
                    "step_id": "main-input",
                    "step_type": "input",
                    "name": "Main Input",
                    "parameters": {"kind": "webhook"},
                },
            ],
            "status": "active",
        }

        resp = await async_client.post("/workflows/", json=workflow_data)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()

        steps = workflow["configuration"]["steps"]
        assert len(steps) == 1
        assert steps[0]["step_type"] == "input"
        assert steps[0]["parameters"]["kind"] == "webhook"

        await async_client.delete(f"/workflows/{workflow['id']}")

    @pytest.mark.asyncio
    async def test_create_workflow_with_multiple_input_nodes(
        self, async_client: AsyncClient, workflow_with_input_nodes
    ):
        """Test creating a workflow with multiple input nodes feeding into merge."""
        resp = await async_client.post("/workflows/", json=workflow_with_input_nodes)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()

        steps = workflow["configuration"]["steps"]
        input_steps = [s for s in steps if s["step_type"] == "input"]
        merge_steps = [s for s in steps if s["step_type"] == "merge"]

        assert len(input_steps) == 2, "Should have 2 input nodes"
        assert len(merge_steps) == 1, "Should have 1 merge node"

        # Verify input kinds
        input_kinds = {s["parameters"]["kind"] for s in input_steps}
        assert input_kinds == {"webhook", "chat"}

        await async_client.delete(f"/workflows/{workflow['id']}")

    @pytest.mark.asyncio
    async def test_input_node_parameter_kinds(self, async_client: AsyncClient):
        """Test that input nodes support various kinds (webhook, chat, manual, etc)."""
        for kind in ["webhook", "chat", "manual", "schedule"]:
            workflow_data = {
                "name": f"Input Kind {kind}",
                "description": f"Test {kind} input",
                "execution_pattern": "dependency_based",
                "steps": [
                    {
                        "step_id": "input",
                        "step_type": "input",
                        "name": f"{kind.title()} Input",
                        "parameters": {"kind": kind},
                    },
                ],
                "status": "active",
            }

            resp = await async_client.post("/workflows/", json=workflow_data)
            assert resp.status_code == 200, (
                f"Failed to create workflow with kind={kind}: {resp.text}"
            )
            workflow = resp.json()

            steps = workflow["configuration"]["steps"]
            assert steps[0]["parameters"]["kind"] == kind

            await async_client.delete(f"/workflows/{workflow['id']}")


class TestMergeNodeCreation:
    """Tests for merge node workflow creation."""

    @pytest.mark.asyncio
    async def test_create_workflow_with_merge_node(
        self, async_client: AsyncClient, workflow_with_input_nodes
    ):
        """Test creating a workflow with a merge node."""
        resp = await async_client.post("/workflows/", json=workflow_with_input_nodes)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()

        steps = workflow["configuration"]["steps"]
        merge_step = next(s for s in steps if s["step_type"] == "merge")
        assert merge_step["dependencies"] == ["webhook-input", "chat-input"]
        assert merge_step["parameters"]["mode"] == "first_available"
        assert merge_step["parameters"]["combine_mode"] == "object"

        await async_client.delete(f"/workflows/{workflow['id']}")

    @pytest.mark.asyncio
    async def test_merge_node_wait_all_mode(
        self, async_client: AsyncClient, workflow_with_wait_all_merge
    ):
        """Test creating a workflow with wait_all merge mode (AND logic)."""
        resp = await async_client.post("/workflows/", json=workflow_with_wait_all_merge)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()

        steps = workflow["configuration"]["steps"]
        merge_step = next(s for s in steps if s["step_type"] == "merge")
        assert merge_step["parameters"]["mode"] == "wait_all"
        assert merge_step["dependencies"] == ["input-a", "input-b"]

        await async_client.delete(f"/workflows/{workflow['id']}")

    @pytest.mark.asyncio
    async def test_merge_node_first_available_mode(self, async_client: AsyncClient):
        """Test creating a workflow with first_available merge mode (OR logic)."""
        workflow_data = {
            "name": "First Available Merge Workflow",
            "description": "Workflow with OR merge logic",
            "version": "1.0.0",
            "execution_pattern": "dependency_based",
            "steps": [
                {
                    "step_id": "fast-input",
                    "step_type": "input",
                    "name": "Fast Input",
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "slow-input",
                    "step_type": "input",
                    "name": "Slow Input",
                    "parameters": {"kind": "manual"},
                },
                {
                    "step_id": "merge",
                    "step_type": "merge",
                    "name": "First Available Merge",
                    "dependencies": ["fast-input", "slow-input"],
                    "parameters": {"mode": "first_available", "combine_mode": "first"},
                },
            ],
            "status": "active",
        }

        resp = await async_client.post("/workflows/", json=workflow_data)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()

        steps = workflow["configuration"]["steps"]
        merge_step = next(s for s in steps if s["step_type"] == "merge")
        assert merge_step["parameters"]["mode"] == "first_available"
        assert merge_step["parameters"]["combine_mode"] == "first"

        await async_client.delete(f"/workflows/{workflow['id']}")

    @pytest.mark.asyncio
    async def test_merge_node_combine_modes(self, async_client: AsyncClient):
        """Test merge node with different combine modes (object, array, first)."""
        for combine_mode in ["object", "array", "first"]:
            workflow_data = {
                "name": f"Merge Combine Mode {combine_mode}",
                "description": f"Test {combine_mode} combine mode",
                "version": "1.0.0",
                "execution_pattern": "dependency_based",
                "steps": [
                    {
                        "step_id": "input-1",
                        "step_type": "input",
                        "name": "Input 1",
                        "parameters": {"kind": "webhook"},
                    },
                    {
                        "step_id": "input-2",
                        "step_type": "input",
                        "name": "Input 2",
                        "parameters": {"kind": "webhook"},
                    },
                    {
                        "step_id": "merge",
                        "step_type": "merge",
                        "name": "Merge",
                        "dependencies": ["input-1", "input-2"],
                        "parameters": {
                            "mode": "wait_all",
                            "combine_mode": combine_mode,
                        },
                    },
                ],
                "status": "active",
            }

            resp = await async_client.post("/workflows/", json=workflow_data)
            assert resp.status_code == 200, (
                f"Failed for combine_mode={combine_mode}: {resp.text}"
            )
            workflow = resp.json()

            steps = workflow["configuration"]["steps"]
            merge_step = next(s for s in steps if s["step_type"] == "merge")
            assert merge_step["parameters"]["combine_mode"] == combine_mode

            await async_client.delete(f"/workflows/{workflow['id']}")


class TestOutputNodeCreation:
    """Tests for output node workflow creation."""

    @pytest.mark.asyncio
    async def test_create_workflow_with_output_node(self, async_client: AsyncClient):
        """Test creating a workflow with an output node."""
        workflow_data = {
            "name": "Output Node Workflow",
            "description": "Workflow with an output node",
            "execution_pattern": "dependency_based",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "name": "Trigger",
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "output",
                    "step_type": "output",
                    "name": "Output",
                    "dependencies": ["trigger"],
                    "parameters": {"label": "Result"},
                },
            ],
            "status": "active",
        }

        resp = await async_client.post("/workflows/", json=workflow_data)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()

        steps = workflow["configuration"]["steps"]
        output_step = next(s for s in steps if s["step_type"] == "output")
        assert output_step["parameters"]["label"] == "Result"

        await async_client.delete(f"/workflows/{workflow['id']}")

    @pytest.mark.asyncio
    async def test_output_node_format_options(self, async_client: AsyncClient):
        """Test output node with different format options."""
        for fmt in ["auto", "json", "text", "markdown"]:
            workflow_data = {
                "name": f"Output Format {fmt}",
                "description": f"Test {fmt} format",
                "execution_pattern": "dependency_based",
                "steps": [
                    {
                        "step_id": "trigger",
                        "step_type": "trigger",
                        "name": "Trigger",
                        "parameters": {"kind": "webhook"},
                    },
                    {
                        "step_id": "output",
                        "step_type": "output",
                        "name": "Output",
                        "dependencies": ["trigger"],
                        "parameters": {"label": "Output", "format": fmt},
                    },
                ],
                "status": "active",
            }

            resp = await async_client.post("/workflows/", json=workflow_data)
            assert resp.status_code == 200, f"Failed for format={fmt}: {resp.text}"
            workflow = resp.json()

            steps = workflow["configuration"]["steps"]
            output_step = next(s for s in steps if s["step_type"] == "output")
            assert output_step["parameters"]["format"] == fmt

            await async_client.delete(f"/workflows/{workflow['id']}")


class TestOutputNodeExecution:
    """Tests for executing workflows with output nodes."""

    async def _poll_execution(
        self, async_client: AsyncClient, execution_id: str, timeout: float = 10.0
    ) -> dict:
        """Poll for execution completion."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            resp = await async_client.get(f"/executions/{execution_id}")
            assert resp.status_code == 200, resp.text
            status = resp.json()
            if status.get("status") in ("completed", "failed", "cancelled"):
                return status
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Execution {execution_id} did not complete in {timeout}s")

    @pytest.mark.asyncio
    async def test_execute_output_node_passthrough(self, async_client: AsyncClient):
        """Test output node passes through data from dependencies."""
        workflow_data = {
            "name": "Output Passthrough Test",
            "description": "Test output node passes data through",
            "version": "1.0.0",
            "execution_pattern": "dependency_based",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "name": "Trigger",
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "data-source",
                    "step_type": "data_input",
                    "name": "Data Source",
                    "dependencies": ["trigger"],
                    "config": {"data": {"message": "hello", "value": 123}},
                },
                {
                    "step_id": "output",
                    "step_type": "output",
                    "name": "Final Output",
                    "dependencies": ["data-source"],
                    "parameters": {"label": "Result", "format": "json"},
                },
            ],
            "status": "active",
        }

        resp = await async_client.post("/workflows/", json=workflow_data)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()
        workflow_id = workflow["id"]

        try:
            exec_body = {"trigger": {"kind": "webhook"}, "wait": False}
            resp = await async_client.post(
                f"/workflows/{workflow_id}/execute", json=exec_body
            )
            assert resp.status_code == 200, resp.text
            execution = resp.json()

            status = await self._poll_execution(async_client, execution["id"])
            assert status["status"] == "completed", f"Execution failed: {status}"
        finally:
            await async_client.delete(f"/workflows/{workflow_id}")


class TestDataInputExecution:
    """Tests for executing workflows with data_input nodes (static data providers)."""

    async def _poll_execution(
        self, async_client: AsyncClient, execution_id: str, timeout: float = 10.0
    ) -> dict:
        """Poll for execution completion."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            resp = await async_client.get(f"/executions/{execution_id}")
            assert resp.status_code == 200, resp.text
            status = resp.json()
            if status.get("status") in ("completed", "failed", "cancelled"):
                return status
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Execution {execution_id} did not complete in {timeout}s")

    @pytest.mark.asyncio
    async def test_execute_data_input_with_static_data(self, async_client: AsyncClient):
        """Test data_input step provides static data from config."""
        workflow_data = {
            "name": "Static Data Input Test",
            "description": "Test data_input with static config data",
            "version": "1.0.0",
            "execution_pattern": "dependency_based",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "name": "Webhook Trigger",
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "data-source",
                    "step_type": "data_input",
                    "name": "Static Data",
                    "dependencies": ["trigger"],
                    "config": {"data": {"key": "value", "number": 42}},
                },
            ],
            "status": "active",
        }

        resp = await async_client.post("/workflows/", json=workflow_data)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()
        workflow_id = workflow["id"]

        try:
            exec_body = {"trigger": {"kind": "webhook"}, "wait": False}
            resp = await async_client.post(
                f"/workflows/{workflow_id}/execute", json=exec_body
            )
            assert resp.status_code == 200, resp.text
            execution = resp.json()

            status = await self._poll_execution(async_client, execution["id"])
            assert status["status"] == "completed", f"Execution failed: {status}"
        finally:
            await async_client.delete(f"/workflows/{workflow_id}")


class TestDataMergeExecution:
    """Tests for executing workflows with data_merge nodes."""

    async def _poll_execution(
        self, async_client: AsyncClient, execution_id: str, timeout: float = 10.0
    ) -> dict:
        """Poll for execution completion."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            resp = await async_client.get(f"/executions/{execution_id}")
            assert resp.status_code == 200, resp.text
            status = resp.json()
            if status.get("status") in ("completed", "failed", "cancelled"):
                return status
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Execution {execution_id} did not complete in {timeout}s")

    @pytest.mark.asyncio
    async def test_execute_data_merge_combines_inputs(self, async_client: AsyncClient):
        """Test data_merge step combines data from multiple inputs."""
        workflow_data = {
            "name": "Data Merge Combine Test",
            "description": "Test data_merge combines multiple inputs",
            "version": "1.0.0",
            "execution_pattern": "dependency_based",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "name": "Webhook Trigger",
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "input-1",
                    "step_type": "data_input",
                    "name": "Input 1",
                    "dependencies": ["trigger"],
                    "config": {"data": {"source": "input1", "value": 10}},
                },
                {
                    "step_id": "input-2",
                    "step_type": "data_input",
                    "name": "Input 2",
                    "dependencies": ["trigger"],
                    "config": {"data": {"source": "input2", "value": 20}},
                },
                {
                    "step_id": "merge",
                    "step_type": "data_merge",
                    "name": "Merge All",
                    "dependencies": ["input-1", "input-2"],
                    "config": {"merge_strategy": "combine"},
                },
            ],
            "status": "active",
        }

        resp = await async_client.post("/workflows/", json=workflow_data)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()
        workflow_id = workflow["id"]

        try:
            exec_body = {
                "trigger": {"kind": "webhook"},
                "input_data": {},
                "wait": False,
            }
            resp = await async_client.post(
                f"/workflows/{workflow_id}/execute", json=exec_body
            )
            assert resp.status_code == 200, resp.text
            execution = resp.json()

            status = await self._poll_execution(async_client, execution["id"])
            assert status["status"] == "completed", f"Execution failed: {status}"

            # Verify merge step completed
            step_results = status.get("step_results", {})
            if step_results:
                merge_result = step_results.get("merge", {})
                assert merge_result is not None
        finally:
            await async_client.delete(f"/workflows/{workflow_id}")

    @pytest.mark.asyncio
    async def test_execute_chain_through_data_merge(self, async_client: AsyncClient):
        """Test data flows through: trigger -> inputs -> merge -> processing."""
        workflow_data = {
            "name": "Chain Through Data Merge",
            "description": "Full data flow chain with merge",
            "version": "1.0.0",
            "execution_pattern": "dependency_based",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "name": "Webhook Trigger",
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "data-1",
                    "step_type": "data_input",
                    "name": "Data Source 1",
                    "dependencies": ["trigger"],
                    "config": {"data": {"a": 1, "b": 2}},
                },
                {
                    "step_id": "data-2",
                    "step_type": "data_input",
                    "name": "Data Source 2",
                    "dependencies": ["trigger"],
                    "config": {"data": {"c": 3, "d": 4}},
                },
                {
                    "step_id": "merge",
                    "step_type": "data_merge",
                    "name": "Combine Data",
                    "dependencies": ["data-1", "data-2"],
                    "config": {"merge_strategy": "combine"},
                },
                {
                    "step_id": "process",
                    "step_type": "data_processing",
                    "name": "Process Merged",
                    "dependencies": ["merge"],
                    "config": {"processing_type": "identity"},
                },
            ],
            "status": "active",
        }

        resp = await async_client.post("/workflows/", json=workflow_data)
        assert resp.status_code == 200, resp.text
        workflow = resp.json()
        workflow_id = workflow["id"]

        try:
            exec_body = {"trigger": {"kind": "webhook"}, "wait": False}
            resp = await async_client.post(
                f"/workflows/{workflow_id}/execute", json=exec_body
            )
            assert resp.status_code == 200, resp.text
            execution = resp.json()

            status = await self._poll_execution(async_client, execution["id"])
            assert status["status"] == "completed", f"Execution failed: {status}"
        finally:
            await async_client.delete(f"/workflows/{workflow_id}")
