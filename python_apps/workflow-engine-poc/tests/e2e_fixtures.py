"""
Reusable E2E fixtures for workflows, agents, and prompts used by interactive tests.

These are plain Python dicts intended to be posted to the workflow-engine-poc API.

Usage example in tests/scripts:

    from workflow_engine_poc.tests.e2e_fixtures import WORKFLOWS

    wf = WORKFLOWS["interactive_two_agents"]
    # optionally deepcopy and tweak

Keep these fixtures minimal and API-ready.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

# -----------------------------------------------------------------------------
# Agent and Prompt placeholders (not strictly required by current tests)
# -----------------------------------------------------------------------------

AGENTS: Mapping[str, Dict[str, Any]] = {
    # Logical agent descriptors used in workflows; no DB creation required for tests
    "Clarifier": {
        "name": "Clarifier",
        "system_prompt": "Ask clarifying questions before answering.",
    },
    "Analyzer": {
        "name": "Analyzer",
        "system_prompt": "Analyze the prior agent's output.",
    },
}

PROMPTS: Mapping[str, Dict[str, Any]] = {
    # Placeholder prompt definitions (unused directly by tests for now)
    "clarifier_sys": {
        "name": "clarifier_sys",
        "content": "Ask clarifying questions before answering.",
    },
    "analyzer_sys": {
        "name": "analyzer_sys",
        "content": "Analyze the prior agent's output.",
    },
}

# -----------------------------------------------------------------------------
# Workflow fixtures
# -----------------------------------------------------------------------------

# Trigger step used by chat-style workflows
CHAT_TRIGGER_STEP: Dict[str, Any] = {
    "step_id": "trigger",
    "step_type": "trigger",
    "parameters": {
        "kind": "chat",
        "need_history": True,
        "allowed_modalities": ["text"],
    },
}

AGENT1_INTERACTIVE_STEP: Dict[str, Any] = {
    "step_id": "agent_1",
    "step_type": "agent_execution",
    "dependencies": ["trigger"],
    "config": {
        "agent_name": AGENTS["Clarifier"]["name"],
        "system_prompt": AGENTS["Clarifier"]["system_prompt"],
        "query": "{current_message}",
        "multi_turn": True,
        # interactive defaults to True; keeping explicit for clarity
        "interactive": True,
    },
}

AGENT2_NON_INTERACTIVE_STEP: Dict[str, Any] = {
    "step_id": "agent_2",
    "step_type": "agent_execution",
    "dependencies": ["agent_1"],
    "config": {
        "agent_name": AGENTS["Analyzer"]["name"],
        "system_prompt": AGENTS["Analyzer"]["system_prompt"],
        "query": "Analyze: {agent_1}",
        "interactive": False,
    },
    "input_mapping": {"agent_1": "agent_1"},
}

AGENT2_INTERACTIVE_STEP: Dict[str, Any] = {
    "step_id": "agent_2",
    "step_type": "agent_execution",
    "dependencies": ["agent_1"],
    "config": {
        "agent_name": AGENTS["Analyzer"]["name"],
        "system_prompt": AGENTS["Analyzer"]["system_prompt"],
        "query": "Analyze: {agent_1}",
        "interactive": True,
        "multi_turn": True,
    },
    "input_mapping": {"agent_1": "agent_1"},
}

WORKFLOWS: Mapping[str, Dict[str, Any]] = {
    # Agent 1 pauses; Agent 2 runs automatically after Agent 1 completes
    "interactive_agent1_only": {
        "name": "Interactive Agent 1 Only",
        "description": "Agent 1 pauses for user input, Agent 2 runs to analyze.",
        "steps": [deepcopy(CHAT_TRIGGER_STEP), deepcopy(AGENT1_INTERACTIVE_STEP), deepcopy(AGENT2_NON_INTERACTIVE_STEP)],
    },
    # Both agents are interactive and multi-turn
    "interactive_two_agents": {
        "name": "Interactive Two Agents",
        "description": "Agent 1 pauses for user input, Agent 2 depends on Agent 1 and pauses as well.",
        "steps": [deepcopy(CHAT_TRIGGER_STEP), deepcopy(AGENT1_INTERACTIVE_STEP), deepcopy(AGENT2_INTERACTIVE_STEP)],
    },
}


def build_workflow(key: str, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return a deep-copied workflow fixture, optionally applying overrides."""
    if key not in WORKFLOWS:
        raise KeyError(f"Unknown workflow key: {key}")
    wf = deepcopy(WORKFLOWS[key])
    if overrides:
        # Shallow-merge at top-level for simplicity
        wf.update(overrides)
    return wf


def list_workflows() -> list[str]:
    """List available workflow fixture keys."""
    return list(WORKFLOWS.keys())

