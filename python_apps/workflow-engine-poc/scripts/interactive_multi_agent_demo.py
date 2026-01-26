"""
Interactive multi-agent demo via API (synchronous script)

Requires the workflow-engine-poc FastAPI server running on port 8006.

Run:
  python python_apps/workflow-engine-poc/scripts/interactive_multi_agent_demo.py
"""

import time
import json
import httpx

API_BASE_URL = "http://localhost:8006"


def check_api_health(client: httpx.Client) -> bool:
    try:
        resp = client.get(f"{API_BASE_URL}/health")
        return resp.status_code == 200
    except Exception:
        return False


def create_workflow(client: httpx.Client, config: dict) -> str:
    resp = client.post(f"{API_BASE_URL}/workflows/", json=config, follow_redirects=True)
    resp.raise_for_status()
    data = resp.json()
    return data["id"]


def execute_workflow(client: httpx.Client, workflow_id: str, body: dict) -> str:
    resp = client.post(
        f"{API_BASE_URL}/workflows/{workflow_id}/execute/local",
        json=body,
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def get_status(client: httpx.Client, execution_id: str) -> dict:
    resp = client.get(f"{API_BASE_URL}/executions/{execution_id}")
    resp.raise_for_status()
    return resp.json()


def get_results(client: httpx.Client, execution_id: str) -> dict:
    resp = client.get(f"{API_BASE_URL}/executions/{execution_id}/results")
    resp.raise_for_status()
    return resp.json()


def get_step_state(results: dict, step_id: str) -> str | None:
    step_results = results.get("step_results") or {}
    step = step_results.get(step_id)
    if not step:
        return None
    return step.get("status")


def wait_for_step_state(
    client: httpx.Client,
    execution_id: str,
    step_id: str,
    desired: tuple[str, ...] = ("completed", "failed"),
    timeout_s: float = 20.0,
    interval_s: float = 0.5,
) -> dict:
    """Poll results until a step enters one of the desired states or timeout."""
    deadline = time.time() + timeout_s
    last = None
    res: dict | None = None
    while time.time() < deadline:
        res = get_results(client, execution_id)
        state = get_step_state(res, step_id) or "unknown"
        if state != last:
            print(f"Step {step_id} state: {state}")
            last = state
        if state in desired:
            return res
        time.sleep(interval_s)
    return res or {}


def post_message(
    client: httpx.Client,
    execution_id: str,
    step_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    resp = client.post(
        f"{API_BASE_URL}/executions/{execution_id}/steps/{step_id}/messages",
        json={"role": role, "content": content, "metadata": metadata or {}},
    )
    resp.raise_for_status()
    return resp.json()


def list_messages(client: httpx.Client, execution_id: str, step_id: str) -> list[dict]:
    resp = client.get(
        f"{API_BASE_URL}/executions/{execution_id}/steps/{step_id}/messages",
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp.json()


def print_step_outputs(results: dict) -> None:
    step_results = results.get("step_results") or {}
    print("\n=== Step Outputs ===")
    for step_id, res in step_results.items():
        print(
            f"- {step_id}: status={res.get('status')} time={res.get('execution_time_ms')}ms"
        )
        out = res.get("output_data")
        if isinstance(out, dict):
            # Prefer agent_response (from WAITING multi-turn) then response (from final)
            agent_response = out.get("agent_response")
            if isinstance(agent_response, dict):
                # Some steps return nested response
                nested_resp = agent_response.get("response") or agent_response.get(
                    "output"
                )
                if nested_resp is not None:
                    print("  agent response:")
                    print(str(nested_resp))
            response = out.get("response")
            if response is not None:
                print("  agent response:")
                print(str(response))
            else:
                print("  output_data:")
                print(json.dumps(out, indent=2))
        else:
            print(f"  output_data: {out}")


def main() -> int:
    with httpx.Client(timeout=30.0) as client:
        if not check_api_health(client):
            print("API not reachable at http://localhost:8006. Start the server first.")
            return 1

        # Build workflow with trigger + two interactive agents
        wf = {
            "name": "Interactive Multi-Agent (Script)",
            "description": "Agent 1 pauses for user input, Agent 2 depends on Agent 1 and pauses as well",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "parameters": {
                        "kind": "chat",
                        "need_history": True,
                        "allowed_modalities": ["text"],
                    },
                },
                {
                    "step_id": "agent_1",
                    "step_type": "agent_execution",
                    "dependencies": ["trigger"],
                    "config": {
                        "agent_name": "Clarifier",
                        "system_prompt": "Ask clarifying questions before answering.",
                        "query": "{current_message}",
                        "multi_turn": True,
                    },
                },
                {
                    "step_id": "agent_2",
                    "step_type": "agent_execution",
                    "dependencies": ["agent_1"],
                    "config": {
                        "agent_name": "Analyzer",
                        "system_prompt": "Analyze the prior agent's output.",
                        "query": "Analyze: {agent_1}",
                        "interactive": True,
                        "multi_turn": True,
                    },
                    "input_mapping": {"agent_1": "agent_1"},
                },
            ],
        }

        print("Creating workflow...")
        workflow_id = create_workflow(client, wf)
        print(f"Workflow ID: {workflow_id}")

        print("Starting execution (local backend, wait=false)...")
        execution_id = execute_workflow(
            client,
            workflow_id,
            {
                "trigger": {"kind": "chat"},
                # Provide an initial user message so the first agent has a non-empty query
                "query": "Research AI trends in healthcare",
                "wait": False,
            },
        )
        print(f"Execution ID: {execution_id}")

        # Poll until running/waiting
        last = None
        for _ in range(20):
            s = get_status(client, execution_id)
            if s != last:
                print(
                    f"Status: {s.get('status')}  current_step={s.get('current_step')}  completed_steps={s.get('completed_steps')}"
                )
                last = s
            if s.get("status") in ("running", "waiting"):
                break
            time.sleep(0.5)

        # Send messages to agent_1
        print("\nSending messages to agent_1...")
        post_message(
            client, execution_id, "agent_1", "user", "Research AI trends in healthcare"
        )
        time.sleep(0.3)
        # Wait until agent_1 first emits an agent_response (WAITING state)
        res = wait_for_step_state(client, execution_id, "agent_1", ("waiting",))
        print_step_outputs(res)

        post_message(
            client,
            execution_id,
            "agent_1",
            "user",
            "That's enough, proceed.",
            {"final_turn": True},
        )
        # Wait until agent_1 completes
        res = wait_for_step_state(
            client, execution_id, "agent_1", ("completed", "failed")
        )
        print_step_outputs(res)

        # Now agent_2 will wait as well
        print("\nSending messages to agent_2...")
        time.sleep(0.3)
        post_message(client, execution_id, "agent_2", "user", "Analyze now.")
        res = wait_for_step_state(client, execution_id, "agent_2", ("waiting",))
        print_step_outputs(res)

        post_message(
            client, execution_id, "agent_2", "user", "Finalize.", {"final_turn": True}
        )
        res = wait_for_step_state(
            client, execution_id, "agent_2", ("completed", "failed")
        )
        print_step_outputs(res)

        # Wait for completion, printing status changes
        print("\nWaiting for completion...")
        last_status = None
        for _ in range(60):
            last_status = get_status(client, execution_id)
            print(
                f"Status: {last_status.get('status')}  current_step={last_status.get('current_step')}  completed_steps={last_status.get('completed_steps')}"
            )
            if last_status.get("status") in ("completed", "failed", "cancelled"):
                break
            time.sleep(0.5)

        if not last_status or last_status.get("status") != "completed":
            print("Execution did not complete:", json.dumps(last_status, indent=2))
            return 2

        # Fetch and print final execution results
        results = get_results(client, execution_id)
        print_step_outputs(results)

        # Print stored messages for both agents
        print("\n=== Stored Messages ===")
        for sid in ("agent_1", "agent_2"):
            msgs = list_messages(client, execution_id, sid)
            print(f"- {sid}: {len(msgs)} messages")
            for m in msgs[-4:]:  # last few
                print(f"  [{m.get('role')}] {m.get('content')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
