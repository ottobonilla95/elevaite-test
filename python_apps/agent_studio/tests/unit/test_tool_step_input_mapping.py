"""
Unit tests for tool step input mapping in agent_studio

Tests that the $prev expansion and input mapping work correctly
when workflows have Agent -> Tool1 -> Tool2 patterns.

Bug context: Second tool step was incorrectly receiving input from all previous
steps instead of just the immediate predecessor (Tool1).
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock


class TestRequestAdapterInputMapping:
    """Tests for request adapter's input_mapping setup"""

    def test_tool_step_input_mapping_uses_prev(self):
        """Test that request adapter sets up $prev for tool steps"""
        from adapters.request_adapter import RequestAdapter

        agent_id = str(uuid.uuid4())
        tool1_id = str(uuid.uuid4())
        tool2_id = str(uuid.uuid4())

        # Create a workflow config with agent -> tool1 -> tool2
        # This is the Agent Studio format that gets converted by adapt_workflow_create_request
        workflow_config = {
            "name": "Test Workflow",
            "configuration": {
                "agents": [
                    {
                        "agent_id": agent_id,
                        "name": "TestAgent",
                        "agent_type": "router",  # Use a valid agent type
                        "node_type": "agent",
                        "config": {},
                    },
                    {
                        "agent_id": tool1_id,
                        "name": "Tool1",
                        "node_type": "tool",
                        "config": {"tool_name": "calculate"},
                    },
                    {
                        "agent_id": tool2_id,
                        "name": "Tool2",
                        "node_type": "tool",
                        "config": {"tool_name": "calculate"},
                    },
                ],
                "connections": [
                    {
                        "source_agent_id": agent_id,
                        "target_agent_id": tool1_id,
                        "connection_type": "default",
                    },
                    {
                        "source_agent_id": tool1_id,
                        "target_agent_id": tool2_id,
                        "connection_type": "default",
                    },
                ],
            },
        }

        # Adapt the request using the create request adapter
        sdk_request = RequestAdapter.adapt_workflow_create_request(workflow_config)

        # Find the tool steps
        steps = sdk_request["configuration"]["steps"]
        tool1_step = next((s for s in steps if s["step_id"] == tool1_id), None)
        tool2_step = next((s for s in steps if s["step_id"] == tool2_id), None)

        # Verify tool1 has $prev in its top-level input_mapping (not config.input_mapping)
        assert tool1_step is not None, "tool1_step should exist"
        assert tool1_step.get("input_mapping", {}).get("response") == "$prev", (
            f"Tool1 should have input_mapping.response = $prev, got {tool1_step.get('input_mapping')}"
        )

        # Verify tool2 has $prev in its top-level input_mapping
        assert tool2_step is not None, "tool2_step should exist"
        assert tool2_step.get("input_mapping", {}).get("response") == "$prev", (
            f"Tool2 should have input_mapping.response = $prev, got {tool2_step.get('input_mapping')}"
        )

        # Verify dependencies are correct
        assert agent_id in tool1_step.get("dependencies", []), (
            f"Tool1 should depend on agent, got {tool1_step.get('dependencies')}"
        )
        assert tool1_id in tool2_step.get("dependencies", []), (
            f"Tool2 should depend on tool1, got {tool2_step.get('dependencies')}"
        )


class TestPrevExpansionInWorkflowEndpoint:
    """Tests for the $prev expansion logic in workflow_endpoints.py"""

    def test_prev_expansion_for_chained_tool_steps(self):
        """
        Test that $prev is correctly expanded for each tool step
        to reference only its immediate predecessor.
        """
        # Simulate what workflow_endpoints.py does for $prev expansion
        steps = [
            {
                "step_id": "agent",
                "step_type": "agent_execution",
                "dependencies": [],
                "config": {},
            },
            {
                "step_id": "tool1",
                "step_type": "tool_execution",
                "dependencies": ["agent"],
                "config": {"input_mapping": {"response": "$prev"}},
            },
            {
                "step_id": "tool2",
                "step_type": "tool_execution",
                "dependencies": ["tool1"],
                "config": {"input_mapping": {"response": "$prev"}},
            },
        ]

        # Build incoming graph
        step_by_id = {s["step_id"]: s for s in steps}
        incoming = {s["step_id"]: list(s.get("dependencies", [])) for s in steps}

        # Expand $prev references (same logic as workflow_endpoints.py)
        for s in steps:
            sid = s["step_id"]
            if "config" not in s:
                s["config"] = {}

            deps = s.get("dependencies", [])
            unique_dep = None
            if len(deps) == 1:
                unique_dep = deps[0]
            elif len(incoming.get(sid, [])) == 1:
                unique_dep = incoming[sid][0]

            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}

            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str) and unique_dep:
                        if v == "$prev":
                            new_imap[k] = unique_dep
                        elif v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap

        # Verify expansions
        tool1 = step_by_id["tool1"]
        tool2 = step_by_id["tool2"]

        assert tool1["input_mapping"] == {"response": "agent"}, (
            f"Tool1 $prev should expand to 'agent', got {tool1['input_mapping']}"
        )

        assert tool2["input_mapping"] == {"response": "tool1"}, (
            f"Tool2 $prev should expand to 'tool1', got {tool2['input_mapping']}"
        )


class TestEndToEndInputMappingIsolation:
    """
    End-to-end tests that simulate the full flow:
    1. Request adapter creates workflow config with $prev
    2. workflow_endpoints.py expands $prev to actual step IDs
    3. ExecutionContext.get_step_input_data() returns only the mapped data
    """

    def test_full_flow_agent_tool1_tool2(self):
        """
        Test the complete flow from request adapter through execution.

        Bug scenario: Second tool step was receiving input from all previous steps
        instead of just the immediate predecessor.
        """
        from adapters.request_adapter import RequestAdapter
        from workflow_core_sdk.execution_context import ExecutionContext

        agent_id = str(uuid.uuid4())
        tool1_id = str(uuid.uuid4())
        tool2_id = str(uuid.uuid4())

        # Step 1: Create workflow using request adapter (simulates workflow creation)
        workflow_config = {
            "name": "Test Workflow",
            "configuration": {
                "agents": [
                    {
                        "agent_id": agent_id,
                        "name": "TestAgent",
                        "agent_type": "router",
                        "node_type": "agent",
                        "config": {},
                    },
                    {
                        "agent_id": tool1_id,
                        "name": "Tool1",
                        "node_type": "tool",
                        "config": {"tool_name": "calculate"},
                    },
                    {
                        "agent_id": tool2_id,
                        "name": "Tool2",
                        "node_type": "tool",
                        "config": {"tool_name": "calculate"},
                    },
                ],
                "connections": [
                    {"source_agent_id": agent_id, "target_agent_id": tool1_id},
                    {"source_agent_id": tool1_id, "target_agent_id": tool2_id},
                ],
            },
        }

        sdk_request = RequestAdapter.adapt_workflow_create_request(workflow_config)
        steps = sdk_request["configuration"]["steps"]

        # Step 2: Simulate workflow_endpoints.py $prev expansion
        step_by_id = {s["step_id"]: s for s in steps}
        incoming = {s["step_id"]: list(s.get("dependencies", [])) for s in steps}

        for s in steps:
            sid = s["step_id"]
            if "config" not in s:
                s["config"] = {}

            deps = s.get("dependencies", [])
            unique_dep = None
            if len(deps) == 1:
                unique_dep = deps[0]
            elif len(incoming.get(sid, [])) == 1:
                unique_dep = incoming[sid][0]

            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}

            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str) and unique_dep:
                        if v == "$prev":
                            new_imap[k] = unique_dep
                        elif v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap

        # Verify $prev was expanded correctly
        tool1_step = step_by_id[tool1_id]
        tool2_step = step_by_id[tool2_id]

        assert tool1_step["input_mapping"] == {"response": agent_id}, (
            f"Tool1 $prev should expand to agent_id, got {tool1_step['input_mapping']}"
        )
        assert tool2_step["input_mapping"] == {"response": tool1_id}, (
            f"Tool2 $prev should expand to tool1_id, got {tool2_step['input_mapping']}"
        )

        # Step 3: Test ExecutionContext.get_step_input_data()
        workflow_config_for_execution = {
            "workflow_id": "test-workflow",
            "steps": steps,
        }

        user_context = MagicMock()
        user_context.user_id = "test-user"
        user_context.session_id = "test-session"
        user_context.organization_id = "test-org"

        context = ExecutionContext(
            workflow_config=workflow_config_for_execution,
            user_context=user_context,
        )

        # Simulate step outputs
        context.step_io_data[agent_id] = {
            "response": "Agent response content",
            "mode": "llm",
            "metadata": {"model": "gpt-4"},
        }
        context.step_io_data[tool1_id] = {
            "result": "Tool 1 calculation result",
            "success": True,
        }

        # Get input data for tool2 - should ONLY contain tool1's data
        tool2_input = context.get_step_input_data(tool2_id)

        # Verify tool2 only gets tool1's data
        assert "response" in tool2_input, f"tool2_input should have 'response' key, got {tool2_input}"
        assert tool2_input["response"] == context.step_io_data[tool1_id], (
            f"tool2 should get tool1's data, got {tool2_input['response']}"
        )

        # Verify tool2 does NOT have agent's data
        assert "Agent response content" not in str(tool2_input), f"tool2 should NOT have agent's data, but got {tool2_input}"


class TestStreamingEndpointInputMappingExpansion:
    """
    Test that simulates the exact workflow retrieval and execution flow
    from the streaming endpoint, including reading from config.input_mapping.
    """

    def test_streaming_endpoint_prev_expansion_with_config_input_mapping(self):
        """
        This test simulates what happens in the streaming endpoint:
        1. Workflow is retrieved from DB with input_mapping in step["config"]["input_mapping"]
        2. The $prev expansion logic reads from config and writes to step["input_mapping"]
        3. ExecutionContext reads from step["input_mapping"] (top-level on the step object)

        Bug: Second tool step was receiving all previous steps' data.
        """
        from workflow_core_sdk.execution_context import ExecutionContext

        agent_id = str(uuid.uuid4())
        tool1_id = str(uuid.uuid4())
        tool2_id = str(uuid.uuid4())

        # Simulate workflow as stored in database (from request adapter)
        # Note: input_mapping is inside config, not top-level
        stored_workflow_steps = [
            {
                "step_id": agent_id,
                "step_type": "agent_execution",
                "name": "Agent",
                "dependencies": [],
                "config": {},
            },
            {
                "step_id": tool1_id,
                "step_type": "tool_execution",
                "name": "Tool1",
                "dependencies": [agent_id],
                "config": {
                    "tool_name": "calculate",
                    "input_mapping": {"response": "$prev"},  # As stored by request adapter
                },
            },
            {
                "step_id": tool2_id,
                "step_type": "tool_execution",
                "name": "Tool2",
                "dependencies": [tool1_id],
                "config": {
                    "tool_name": "calculate",
                    "input_mapping": {"response": "$prev"},  # As stored by request adapter
                },
            },
        ]

        # Build graph from dependencies (as done in streaming endpoint)
        step_by_id = {s["step_id"]: s for s in stored_workflow_steps}
        incoming = {s["step_id"]: list(s.get("dependencies", [])) for s in stored_workflow_steps}

        # Simulate the $prev expansion logic from streaming endpoint
        for s in stored_workflow_steps:
            sid = s["step_id"]
            if "config" not in s:
                s["config"] = {}

            # Resolve unique previous dependency
            deps = s.get("dependencies") or []
            unique_dep = None
            if isinstance(deps, list) and len(deps) == 1:
                unique_dep = deps[0]
            elif len(incoming.get(sid, [])) == 1:
                unique_dep = incoming[sid][0]

            s["config"]["previous_step_id"] = unique_dep

            # Read input_mapping from step or config
            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}

            # Expand $prev references
            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str) and unique_dep:
                        if v == "$prev":
                            new_imap[k] = unique_dep
                        elif v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                # Write expanded mapping to TOP-LEVEL step (not config)
                s["input_mapping"] = new_imap

        # Verify expansion happened correctly
        tool1 = step_by_id[tool1_id]
        tool2 = step_by_id[tool2_id]

        assert tool1["input_mapping"] == {"response": agent_id}, (
            f"Tool1's input_mapping should map to agent_id, got {tool1['input_mapping']}"
        )
        assert tool2["input_mapping"] == {"response": tool1_id}, (
            f"Tool2's input_mapping should map to tool1_id, got {tool2['input_mapping']}"
        )

        # Now test ExecutionContext with this expanded workflow
        workflow_config = {
            "workflow_id": "test-workflow",
            "steps": stored_workflow_steps,
        }

        user_context = MagicMock()
        user_context.user_id = "test-user"
        user_context.session_id = "test-session"
        user_context.organization_id = "test-org"

        context = ExecutionContext(
            workflow_config=workflow_config,
            user_context=user_context,
        )

        # Simulate step outputs
        context.step_io_data[agent_id] = {
            "response": "Agent response - should NOT appear in tool2",
            "mode": "llm",
        }
        context.step_io_data[tool1_id] = {
            "result": "Tool1 result - SHOULD appear in tool2",
            "success": True,
        }

        # Get input data for tool2
        tool2_input = context.get_step_input_data(tool2_id)

        # Verify tool2 only gets tool1's data
        assert "response" in tool2_input, f"tool2_input should have 'response' key, got keys: {list(tool2_input.keys())}"
        assert tool2_input["response"] == context.step_io_data[tool1_id], f"tool2 should get tool1's data via 'response' key"

        # Verify tool2 does NOT have agent's data
        assert "Agent response" not in str(tool2_input), f"tool2 should NOT have agent's response, but got {tool2_input}"


class TestTriggerStepPrevPatch:
    """
    Tests for the patch that handles $prev.response when the previous step is a trigger.

    The trigger step outputs: {kind, messages, current_message, attachments}
    It does NOT have a 'response' field.

    When the UI sets $prev.response on a tool step directly after trigger,
    we patch it to use trigger.current_message instead.
    """

    def test_prev_response_patched_when_prev_is_trigger(self):
        """
        Test that $prev.response is patched to trigger.current_message
        when the previous step is a trigger step.
        """
        trigger_id = str(uuid.uuid4())
        tool_id = str(uuid.uuid4())

        steps = [
            {
                "step_id": trigger_id,
                "step_type": "trigger",
                "dependencies": [],
                "config": {"kind": "chat"},
            },
            {
                "step_id": tool_id,
                "step_type": "tool_execution",
                "dependencies": [trigger_id],
                "config": {
                    "tool_name": "my_tool",
                    "param_mapping": {"query": "$prev.response"},
                    "input_mapping": {"response": "$prev"},
                },
            },
        ]

        # Build graph
        step_by_id = {s["step_id"]: s for s in steps}
        incoming = {s["step_id"]: list(s.get("dependencies", [])) for s in steps}

        # Simulate the expansion logic from workflow_endpoints.py
        for s in steps:
            sid = s["step_id"]
            if "config" not in s:
                s["config"] = {}

            deps = s.get("dependencies", [])
            unique_dep = None
            if len(deps) == 1:
                unique_dep = deps[0]
            elif len(incoming.get(sid, [])) == 1:
                unique_dep = incoming[sid][0]

            # Check if unique_dep is a trigger step
            prev_is_trigger = False
            if unique_dep and unique_dep in step_by_id:
                prev_step = step_by_id[unique_dep]
                prev_step_type = prev_step.get("step_type", "")
                prev_is_trigger = prev_step_type == "trigger"

            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}
            pmap = s["config"].get("param_mapping")

            # Patch param_mapping
            if isinstance(pmap, dict):
                new_pmap = {}
                for k, v in pmap.items():
                    if isinstance(v, str):
                        if prev_is_trigger and v in ("$prev.response", "response"):
                            new_pmap[k] = "trigger.current_message"
                        else:
                            new_pmap[k] = v
                    else:
                        new_pmap[k] = v
                s["config"]["param_mapping"] = new_pmap

            # Patch input_mapping
            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str) and unique_dep:
                        if prev_is_trigger and v in ("$prev", "$prev.response"):
                            new_imap[k] = "trigger"
                        elif v == "$prev":
                            new_imap[k] = unique_dep
                        elif v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap

        # Verify the tool step got patched correctly
        tool_step = step_by_id[tool_id]
        assert tool_step["config"]["param_mapping"] == {"query": "trigger.current_message"}, (
            f"param_mapping should be patched to trigger.current_message, got {tool_step['config']['param_mapping']}"
        )
        assert tool_step["input_mapping"] == {"response": "trigger"}, (
            f"input_mapping should be patched to trigger, got {tool_step['input_mapping']}"
        )

    def test_prev_response_not_patched_when_prev_is_agent(self):
        """
        Test that $prev.response is NOT patched when the previous step is an agent.
        """
        agent_id = str(uuid.uuid4())
        tool_id = str(uuid.uuid4())

        steps = [
            {
                "step_id": agent_id,
                "step_type": "agent_execution",
                "dependencies": [],
                "config": {},
            },
            {
                "step_id": tool_id,
                "step_type": "tool_execution",
                "dependencies": [agent_id],
                "config": {
                    "tool_name": "my_tool",
                    "param_mapping": {"query": "$prev.response"},
                    "input_mapping": {"response": "$prev"},
                },
            },
        ]

        # Build graph
        step_by_id = {s["step_id"]: s for s in steps}
        incoming = {s["step_id"]: list(s.get("dependencies", [])) for s in steps}

        # Simulate the expansion logic
        for s in steps:
            sid = s["step_id"]
            if "config" not in s:
                s["config"] = {}

            deps = s.get("dependencies", [])
            unique_dep = None
            if len(deps) == 1:
                unique_dep = deps[0]

            prev_is_trigger = False
            if unique_dep and unique_dep in step_by_id:
                prev_step = step_by_id[unique_dep]
                prev_is_trigger = prev_step.get("step_type", "") == "trigger"

            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}
            pmap = s["config"].get("param_mapping")

            if isinstance(pmap, dict):
                new_pmap = {}
                for k, v in pmap.items():
                    if isinstance(v, str):
                        if prev_is_trigger and v in ("$prev.response", "response"):
                            new_pmap[k] = "trigger.current_message"
                        else:
                            new_pmap[k] = v
                    else:
                        new_pmap[k] = v
                s["config"]["param_mapping"] = new_pmap

            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str) and unique_dep:
                        if prev_is_trigger and v in ("$prev", "$prev.response"):
                            new_imap[k] = "trigger"
                        elif v == "$prev":
                            new_imap[k] = unique_dep
                        elif v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap

        # Verify the tool step was NOT patched (agent has a response field)
        tool_step = step_by_id[tool_id]
        assert tool_step["config"]["param_mapping"] == {"query": "$prev.response"}, (
            f"param_mapping should NOT be patched for agent, got {tool_step['config']['param_mapping']}"
        )
        assert tool_step["input_mapping"] == {"response": agent_id}, (
            f"input_mapping should expand $prev to agent_id, got {tool_step['input_mapping']}"
        )

    def test_prev_response_patched_when_no_previous_step(self):
        """
        Test that $prev.response is patched to trigger.current_message
        when there is no previous step (unique_dep=None).
        This handles workflows created with just a tool step and no trigger step.
        """
        tool_id = str(uuid.uuid4())

        steps = [
            {
                "step_id": tool_id,
                "step_type": "tool_execution",
                "dependencies": [],  # No dependencies
                "config": {
                    "tool_name": "my_tool",
                    "param_mapping": {"query": "$prev.response"},
                    "input_mapping": {"response": "$prev"},
                },
            },
        ]

        # Build graph
        step_by_id = {s["step_id"]: s for s in steps}
        incoming = {s["step_id"]: list(s.get("dependencies", [])) for s in steps}

        # Simulate the expansion logic from workflow_endpoints.py
        for s in steps:
            sid = s["step_id"]
            if "config" not in s:
                s["config"] = {}

            deps = s.get("dependencies", [])
            unique_dep = None
            if len(deps) == 1:
                unique_dep = deps[0]
            elif len(incoming.get(sid, [])) == 1:
                unique_dep = incoming[sid][0]

            # Check if unique_dep is a trigger step
            prev_is_trigger = False
            if unique_dep and unique_dep in step_by_id:
                prev_step = step_by_id[unique_dep]
                prev_step_type = prev_step.get("step_type", "")
                prev_is_trigger = prev_step_type == "trigger"

            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}
            pmap = s["config"].get("param_mapping")

            # Patch param_mapping - now also handles unique_dep=None case
            if isinstance(pmap, dict):
                new_pmap = {}
                for k, v in pmap.items():
                    if isinstance(v, str):
                        if (prev_is_trigger or unique_dep is None) and v in ("$prev.response", "response"):
                            new_pmap[k] = "trigger.current_message"
                        else:
                            new_pmap[k] = v
                    else:
                        new_pmap[k] = v
                s["config"]["param_mapping"] = new_pmap

            # Patch input_mapping - now also handles unique_dep=None case
            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str):
                        if (prev_is_trigger or unique_dep is None) and v in ("$prev", "$prev.response"):
                            new_imap[k] = "trigger"
                        elif unique_dep and v == "$prev":
                            new_imap[k] = unique_dep
                        elif unique_dep and v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap

        # Verify the tool step got patched correctly even with no previous step
        tool_step = step_by_id[tool_id]
        assert tool_step["config"]["param_mapping"] == {"query": "trigger.current_message"}, (
            f"param_mapping should be patched to trigger.current_message when no prev step, got {tool_step['config']['param_mapping']}"
        )
        assert tool_step["input_mapping"] == {"response": "trigger"}, (
            f"input_mapping should be patched to trigger when no prev step, got {tool_step['input_mapping']}"
        )
