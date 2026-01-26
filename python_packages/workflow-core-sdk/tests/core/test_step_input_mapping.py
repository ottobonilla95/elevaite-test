"""
Unit tests for step input mapping

Tests that steps only receive input from their explicitly mapped dependencies,
NOT from all previous steps in the workflow.

Bug context: When a workflow has Agent -> Tool1 -> Tool2, the second tool step
was incorrectly receiving input from all previous steps instead of just Tool1.
"""

import pytest

from workflow_core_sdk.execution_context import ExecutionContext
from workflow_core_sdk.execution.context_impl import UserContext


@pytest.fixture
def user_context():
    """Create a user context"""
    return UserContext(
        user_id="test-user",
        session_id="test-session",
    )


class TestStepInputMappingIsolation:
    """Tests that step input mapping properly isolates data between steps"""

    def test_second_tool_step_only_receives_input_from_first_tool_step(self, user_context):
        """
        Bug test: Second tool step should only receive input from first tool step,
        not from the agent step.

        Workflow: Agent -> Tool1 -> Tool2
        Tool2 should only see Tool1's output, not Agent's output.
        """
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Agent -> Tool1 -> Tool2 Workflow",
            "steps": [
                {
                    "step_id": "agent_step",
                    "step_type": "agent_execution",
                    "name": "Agent Step",
                    "config": {},
                },
                {
                    "step_id": "tool_step_1",
                    "step_type": "tool_execution",
                    "name": "Tool Step 1",
                    "dependencies": ["agent_step"],
                    "input_mapping": {"response": "agent_step"},
                    "config": {},
                },
                {
                    "step_id": "tool_step_2",
                    "step_type": "tool_execution",
                    "name": "Tool Step 2",
                    "dependencies": ["tool_step_1"],
                    # This is the key: only maps from tool_step_1, NOT from agent_step
                    "input_mapping": {"response": "tool_step_1"},
                    "config": {},
                },
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config, user_context=user_context)

        # Simulate step outputs being stored
        context.step_io_data["agent_step"] = {
            "response": "Agent response text",
            "tool_calls": [],
            "mode": "llm",
        }
        context.step_io_data["tool_step_1"] = {
            "success": True,
            "tool": {"name": "some_tool"},
            "result": "Tool 1 result",
        }

        # Get input data for tool_step_2
        input_data = context.get_step_input_data("tool_step_2")

        # Tool step 2 should ONLY have data from tool_step_1
        assert "response" in input_data, "tool_step_2 should have 'response' key"
        assert input_data["response"] == context.step_io_data["tool_step_1"], (
            "tool_step_2 'response' should be tool_step_1's output"
        )

        # Verify agent_step data is NOT present
        assert "Agent response text" not in str(input_data), "tool_step_2 should NOT contain agent_step's response"

    def test_tool_step_with_prev_expanded_correctly(self, user_context):
        """
        Test that when $prev is expanded to the actual step ID,
        the input mapping works correctly.
        """
        # This simulates what should happen AFTER $prev is expanded
        workflow_config = {
            "workflow_id": "test-workflow",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "config": {}},
                {
                    "step_id": "step2",
                    "step_type": "tool_execution",
                    "dependencies": ["step1"],
                    "input_mapping": {"response": "step1"},  # $prev expanded to step1
                    "config": {},
                },
                {
                    "step_id": "step3",
                    "step_type": "tool_execution",
                    "dependencies": ["step2"],
                    "input_mapping": {"response": "step2"},  # $prev expanded to step2
                    "config": {},
                },
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config, user_context=user_context)

        # Store outputs
        context.step_io_data["step1"] = {"output": "step1 output"}
        context.step_io_data["step2"] = {"output": "step2 output"}

        # Get input for step3
        input_data = context.get_step_input_data("step3")

        # step3 should only have step2's output
        assert input_data.get("response") == {"output": "step2 output"}
        assert "step1 output" not in str(input_data)

    def test_unexpanded_prev_reference_not_resolved(self, user_context):
        """
        Test that if $prev is NOT expanded, the input mapping doesn't work
        (since $prev is not a valid step_id).
        """
        workflow_config = {
            "workflow_id": "test-workflow",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "config": {}},
                {
                    "step_id": "step2",
                    "step_type": "tool_execution",
                    "dependencies": ["step1"],
                    # $prev NOT expanded - this should fail to resolve
                    "input_mapping": {"response": "$prev"},
                    "config": {},
                },
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config, user_context=user_context)
        context.step_io_data["step1"] = {"output": "step1 output"}

        # Get input for step2
        input_data = context.get_step_input_data("step2")

        # Since "$prev" is not a valid step_id, it shouldn't resolve
        assert input_data.get("response") is None, "Unexpanded $prev should not resolve to any data"

    def test_field_path_mapping_only_from_specified_step(self, user_context):
        """
        Test that field path mappings (e.g., step1.result) only access
        the specified step's data.
        """
        workflow_config = {
            "workflow_id": "test-workflow",
            "steps": [
                {"step_id": "agent", "step_type": "agent_execution", "config": {}},
                {
                    "step_id": "tool1",
                    "step_type": "tool_execution",
                    "dependencies": ["agent"],
                    "input_mapping": {"agent_response": "agent.response"},
                    "config": {},
                },
                {
                    "step_id": "tool2",
                    "step_type": "tool_execution",
                    "dependencies": ["tool1"],
                    # Only maps tool1.result, should not see agent data
                    "input_mapping": {"prev_result": "tool1.result"},
                    "config": {},
                },
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config, user_context=user_context)

        context.step_io_data["agent"] = {"response": "Agent says hello", "metadata": {}}
        context.step_io_data["tool1"] = {"result": "Tool 1 computed value", "success": True}

        input_data = context.get_step_input_data("tool2")

        assert input_data.get("prev_result") == "Tool 1 computed value"
        assert "Agent says hello" not in str(input_data)
        assert len(input_data) == 1, "Should only have one mapped key"


class TestPrevExpansionLogic:
    """Tests for the $prev expansion logic that happens in workflow_endpoints.py"""

    def test_expand_prev_for_tool_steps(self, user_context):
        """
        Simulate the $prev expansion that happens in workflow_endpoints.py.
        This tests the logic that transforms $prev to actual step IDs.
        """
        # This is what comes from the request adapter with $prev
        steps_with_prev = [
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
                "config": {
                    "input_mapping": {"response": "$prev"},
                },
            },
            {
                "step_id": "tool2",
                "step_type": "tool_execution",
                "dependencies": ["tool1"],
                "config": {
                    "input_mapping": {"response": "$prev"},
                },
            },
        ]

        # Simulate the $prev expansion logic from workflow_endpoints.py
        def expand_prev_references(steps):
            """Simulate the graph-based $prev expansion"""
            # Build graph
            {s["step_id"]: s for s in steps}
            incoming = {s["step_id"]: list(s.get("dependencies", [])) for s in steps}

            for s in steps:
                sid = s["step_id"]
                if "config" not in s:
                    s["config"] = {}

                # Determine unique_dep
                deps = s.get("dependencies", [])
                unique_dep = None
                if len(deps) == 1:
                    unique_dep = deps[0]
                elif len(incoming.get(sid, [])) == 1:
                    unique_dep = incoming[sid][0]

                # Get input_mapping from step or config
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
                    # Write to top-level input_mapping
                    s["input_mapping"] = new_imap
                else:
                    s["input_mapping"] = imap or {}

            return steps

        # Expand $prev references
        expanded_steps = expand_prev_references(steps_with_prev)

        # Verify tool1's $prev was expanded to "agent"
        tool1 = next(s for s in expanded_steps if s["step_id"] == "tool1")
        assert tool1["input_mapping"] == {"response": "agent"}, (
            f"tool1 should have input_mapping expanded to agent, got {tool1['input_mapping']}"
        )

        # Verify tool2's $prev was expanded to "tool1"
        tool2 = next(s for s in expanded_steps if s["step_id"] == "tool2")
        assert tool2["input_mapping"] == {"response": "tool1"}, (
            f"tool2 should have input_mapping expanded to tool1, got {tool2['input_mapping']}"
        )

        # Now test with ExecutionContext
        workflow_config = {"workflow_id": "test", "steps": expanded_steps}
        context = ExecutionContext(workflow_config=workflow_config, user_context=user_context)

        context.step_io_data["agent"] = {"response": "Agent output", "mode": "llm"}
        context.step_io_data["tool1"] = {"result": "Tool 1 result", "success": True}

        # tool2 should only get tool1's data
        tool2_input = context.get_step_input_data("tool2")
        assert tool2_input.get("response") == context.step_io_data["tool1"]
        assert "Agent output" not in str(tool2_input)

    def test_input_mapping_in_config_vs_top_level(self, user_context):
        """
        Test that input_mapping can be read from either top-level or config,
        but the expanded version should be at top-level.
        """
        # Simulate input_mapping in config (as set by request_adapter)
        steps = [
            {
                "step_id": "step1",
                "step_type": "data_input",
                "dependencies": [],
                "config": {},
            },
            {
                "step_id": "step2",
                "step_type": "tool_execution",
                "dependencies": ["step1"],
                # input_mapping inside config (as request_adapter does it)
                "config": {
                    "input_mapping": {"response": "$prev"},
                },
            },
        ]

        # The code in workflow_endpoints.py reads from config and writes to top-level
        for s in steps:
            imap = s.get("input_mapping") or s.get("config", {}).get("input_mapping") or {}
            deps = s.get("dependencies", [])
            unique_dep = deps[0] if len(deps) == 1 else None

            if isinstance(imap, dict) and unique_dep:
                new_imap = {}
                for k, v in imap.items():
                    if v == "$prev":
                        new_imap[k] = unique_dep
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap

        # Verify expansion happened
        step2 = steps[1]
        assert step2.get("input_mapping") == {"response": "step1"}

        # Verify ExecutionContext reads from top-level
        workflow_config = {"workflow_id": "test", "steps": steps}
        context = ExecutionContext(workflow_config=workflow_config, user_context=user_context)
        context.step_io_data["step1"] = {"output": "step1 data"}

        input_data = context.get_step_input_data("step2")
        assert input_data.get("response") == {"output": "step1 data"}

    def test_input_mapping_fallback_to_config_when_top_level_empty(self, user_context):
        """
        Test that when top-level input_mapping is empty dict, we fall back to config.input_mapping.

        This reproduces the bug where workflows stored in DB have:
        - step["input_mapping"] = {} (empty)
        - step["config"]["input_mapping"] = {"response": "<step_id>"} (actual mapping)
        """
        # Simulate workflow as stored in DB with expanded $prev (but stored in wrong location)
        steps = [
            {"step_id": "agent", "step_type": "agent_execution", "dependencies": [], "config": {}},
            {
                "step_id": "tool1",
                "step_type": "tool_execution",
                "dependencies": ["agent"],
                "input_mapping": {},  # Empty at top-level (this was the bug!)
                "config": {
                    "tool_name": "tool1",
                    "input_mapping": {"response": "agent"},  # Actual mapping is here
                },
            },
            {
                "step_id": "tool2",
                "step_type": "tool_execution",
                "dependencies": ["tool1"],
                "input_mapping": {},  # Empty at top-level (this was the bug!)
                "config": {
                    "tool_name": "tool2",
                    "input_mapping": {"response": "tool1"},  # Should map to tool1, not agent
                },
            },
        ]

        workflow_config = {"workflow_id": "test", "steps": steps}
        context = ExecutionContext(workflow_config=workflow_config, user_context=user_context)
        context.step_io_data["agent"] = {"response": "Agent JSON output - should NOT appear in tool2"}
        context.step_io_data["tool1"] = {"result": "Tool1 calculation result - SHOULD appear in tool2"}

        # Get input for tool2
        tool2_input = context.get_step_input_data("tool2")

        # Verify tool2 gets data from tool1 (via config.input_mapping fallback)
        assert "response" in tool2_input, f"tool2 should have 'response' key, got: {list(tool2_input.keys())}"
        assert tool2_input["response"] == context.step_io_data["tool1"], (
            f"tool2 should get tool1's data, not agent's data. Got: {tool2_input['response']}"
        )

        # Verify tool2 does NOT have agent's data
        assert "Agent JSON output" not in str(tool2_input), f"tool2 should NOT have agent's output. Got: {tool2_input}"
