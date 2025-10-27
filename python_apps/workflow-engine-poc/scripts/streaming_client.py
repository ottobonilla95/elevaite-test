#!/usr/bin/env python3
"""
Simple streaming client for testing workflow-engine-poc streaming endpoints.

Usage:
    python streaming_client.py execution <execution_id>
    python streaming_client.py workflow <workflow_id> [execution_id]
    python streaming_client.py demo
    python streaming_client.py chat <workflow_id>
    python streaming_client.py chat-demo

Examples:
    # Stream specific execution
    python streaming_client.py execution 123e4567-e89b-12d3-a456-426614174000

    # Stream workflow executions
    python streaming_client.py workflow 123e4567-e89b-12d3-a456-426614174000

    # Run a demo (creates workflow, executes it, streams results)
    python streaming_client.py demo

    # Start a chat loop with an existing workflow (chat trigger)
    python streaming_client.py chat 123e4567-e89b-12d3-a456-426614174000

    # Create a chat workflow from fixture and start chat loop
    python streaming_client.py chat-demo
    # Optional backend selector (default local)
    # python streaming_client.py chat-demo --backend dbos

"""

import asyncio
import json
import sys
import time
from datetime import datetime
import contextlib

from pathlib import Path
from typing import Optional

# ANSI color codes
GREY = "\033[90m"
WHITE = "\033[97m"
RESET = "\033[0m"


import httpx

# Configuration
BASE_URL = "http://127.0.0.1:8006"
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "e2e" / "fixtures"


class StreamingClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        # Remember the last waiting step per execution to route user messages correctly
        self._last_waiting_step: dict[str, str] = {}
        # Remember the last step id seen for an execution (any step event)
        self._last_step_id: dict[str, str] = {}

    def _load_fixture(self, filename: str) -> dict:
        """Load a JSON fixture file"""
        fixture_path = FIXTURES_DIR / filename
        with open(fixture_path) as f:
            return json.load(f)

    async def _http_request(self, method: str, path: str, json_body: Optional[dict] = None) -> dict:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, json=json_body)
            response.raise_for_status()
            return response.json()

    def _format_event(self, event: dict) -> str:
        """Format an event for display (non-assistant events in grey)."""
        timestamp = event.get("timestamp", "")
        event_type = event.get("type", "unknown")
        execution_id = event.get("execution_id", "")[:8]  # Short ID

        # Format based on event type
        if event_type == "status":
            status = event.get("data", {}).get("status", "unknown")
            extra = ""
            if "step_count" in event.get("data", {}):
                completed = event.get("data", {}).get("completed_steps", 0)
                total = event.get("data", {}).get("step_count", 0)
                extra = f" ({completed}/{total} steps)"
            return GREY + f"[{timestamp[:19]}] STATUS {execution_id}: {status}{extra}" + RESET

        elif event_type == "step":
            step_id = event.get("data", {}).get("step_id", "unknown")
            step_status = event.get("data", {}).get("step_status", "unknown")
            return GREY + f"[{timestamp[:19]}] STEP   {execution_id}: {step_id} -> {step_status}" + RESET

        elif event_type == "error":
            error = event.get("data", {}).get("error", "unknown error")
            return GREY + f"[{timestamp[:19]}] ERROR  {execution_id}: {error}" + RESET

        elif event_type == "heartbeat":
            return GREY + f"[{timestamp[:19]}] HEARTBEAT" + RESET

        elif event_type == "complete":
            events_sent = event.get("data", {}).get("events_sent", 0)
            return GREY + f"[{timestamp[:19]}] COMPLETE (sent {events_sent} events)" + RESET

        else:
            return GREY + f"[{timestamp[:19]}] {event_type.upper()} {execution_id}: {event.get('data', {})}" + RESET

    def _is_waiting_event(self, event: dict) -> bool:
        """Detect if an event indicates the workflow is waiting for user input."""
        et = (event.get("type") or "").lower()
        data = event.get("data") or {}
        if et == "step":
            st = (data.get("step_status") or "").lower()
            return st == "waiting"
        if et == "status":
            return (data.get("status") or "").lower() == "waiting"
        return False

    def _extract_assistant_text(self, event: dict) -> Optional[dict]:
        """Extract assistant text or delta from a step event payload.
        Returns dict {"type": "delta"|"full", "text": str} or None.
        """
        if event.get("type") != "step":
            return None
        data = event.get("data") or {}
        out = data.get("output_data") if isinstance(data, dict) else None
        if isinstance(out, dict):
            # Streaming delta
            if isinstance(out.get("delta"), str) and out.get("delta"):
                return {"type": "delta", "text": str(out.get("delta"))}
            # Completed agent step shape
            if isinstance(out.get("response"), str) and out.get("response"):
                return {"type": "full", "text": str(out.get("response"))}
            # Waiting agent step shape: { status: "waiting", agent_response: { response: "..." } }
            agent_resp = out.get("agent_response")
            if isinstance(agent_resp, dict) and isinstance(agent_resp.get("response"), str) and agent_resp.get("response"):
                return {"type": "full", "text": str(agent_resp.get("response"))}
        return None

    async def stream_execution(
        self,
        execution_id: str,
        duration: Optional[float] = None,
        stop_on_waiting: bool = False,
        until_assistant: bool = False,
        ignore_initial_waiting: bool = False,
    ):
        """Stream events from a specific execution.
        - stop_on_waiting: stop the stream as soon as a waiting event is seen
        - until_assistant: keep streaming until an assistant line is printed; then stop on next waiting/complete
        - ignore_initial_waiting: ignore waiting events until we see a step/assistant; useful when a stream is opened before sending a user message
        """
        print(f"🔄 Streaming execution {execution_id}")
        print(f"📡 URL: {self.base_url}/executions/{execution_id}/stream")
        print("=" * 80)

        start_time = time.time()
        event_count = 0
        waiting_indicator_printed = False
        assistant_printed = False
        seen_non_status_event = False
        had_delta = False  # track whether we streamed any deltas for the current assistant turn
        current_step_id = None

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("GET", f"{self.base_url}/executions/{execution_id}/stream") as response:
                    if response.status_code != 200:
                        print(f"❌ Stream failed: {response.status_code} {response.text}")
                        return

                    print("✅ Connected! Streaming events...")
                    print()

                    buffer = ""
                    async for chunk in response.aiter_text():
                        if not chunk:
                            continue
                        buffer += chunk
                        # Process complete SSE events delimited by a blank line ("\n\n")
                        while "\n\n" in buffer:
                            block, buffer = buffer.split("\n\n", 1)
                            # Concatenate all data: lines in the block per SSE spec
                            data_lines = [ln[6:] for ln in block.splitlines() if ln.startswith("data: ")]
                            if not data_lines:
                                continue
                            data_str = "\n".join(data_lines)
                            try:
                                event = json.loads(data_str)
                                etype = (event.get("type") or "").lower()
                                if etype == "step":
                                    seen_non_status_event = True
                                    # capture step id for routing next message
                                    exec_id = event.get("execution_id")
                                    step_id = (event.get("data") or {}).get("step_id")
                                    if exec_id and step_id:
                                        self._last_step_id[exec_id] = step_id
                                        current_step_id = step_id
                                # Assistant response or delta
                                a = self._extract_assistant_text(event)
                                if a:
                                    if a.get("type") == "delta":
                                        print(WHITE + a.get("text", ""), end="", flush=True)
                                        had_delta = True
                                    else:
                                        # If we've already printed deltas for this step, don't print the full text again
                                        if not had_delta:
                                            print(WHITE + "Assistant: " + a.get("text", "") + RESET)
                                        waiting_indicator_printed = False
                                        assistant_printed = True
                                        had_delta = False  # reset for next turn
                                        if until_assistant:
                                            print(RESET)
                                            return
                                else:
                                    print(self._format_event(event))
                                    # If we are in a waiting state, show a subtle indicator
                                    if self._is_waiting_event(event):
                                        # Ignore early waiting before a step/assistant arrives if requested
                                        if ignore_initial_waiting and not (assistant_printed or seen_non_status_event):
                                            pass
                                        else:
                                            exec_id = event.get("execution_id")
                                            step_id = (event.get("data") or {}).get("step_id")
                                            if exec_id and step_id:
                                                self._last_waiting_step[exec_id] = step_id
                                            if not waiting_indicator_printed:
                                                print(GREY + "(waiting for next user message…)" + RESET)
                                                waiting_indicator_printed = True
                                            if stop_on_waiting or (until_assistant and assistant_printed):
                                                return
                                event_count += 1

                                # Check for completion
                                if event.get("type") == "complete":
                                    if had_delta:
                                        print(RESET)
                                    print(f"\n🏁 Stream completed after {event_count} events")
                                    return

                            except json.JSONDecodeError:
                                print("⚠️  Malformed event payload")
                                continue

                        # Check duration limit
                        if duration and (time.time() - start_time) > duration:
                            print(f"\n⏰ Duration limit reached ({duration}s)")
                            break

        except KeyboardInterrupt:
            print(f"\n🛑 Interrupted by user after {event_count} events")
        except Exception as e:
            print(f"\n❌ Stream error: {e}")

    async def stream_workflow(self, workflow_id: str, execution_id: Optional[str] = None, duration: Optional[float] = None):
        """Stream events from a workflow"""
        url = f"{self.base_url}/workflows/{workflow_id}/stream"
        if execution_id:
            url += f"?execution_id={execution_id}"

        print(f"🔄 Streaming workflow {workflow_id}")
        if execution_id:
            print(f"🎯 Filtering for execution {execution_id}")
        print(f"📡 URL: {url}")
        print("=" * 80)

        start_time = time.time()
        event_count = 0

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        print(f"❌ Stream failed: {response.status_code} {response.text}")
                        return

                    print("✅ Connected! Streaming events...")
                    print()

                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            lines = chunk.strip().split("\n")
                            for line in lines:
                                if line.startswith("data: "):
                                    try:
                                        event = json.loads(line[6:])
                                        # Assistant response (if present) in white
                                        a = self._extract_assistant_text(event)
                                        if a:
                                            if a.get("type") == "delta":
                                                print(WHITE + a.get("text", ""), end="", flush=True)
                                            else:
                                                print(WHITE + "Assistant: " + a.get("text", "") + RESET)
                                        else:
                                            print(self._format_event(event))
                                        event_count += 1

                                        # Check for completion
                                        if event.get("type") == "complete":
                                            print(f"\n🏁 Stream completed after {event_count} events")
                                            return

                                    except json.JSONDecodeError:
                                        print(f"⚠️  Malformed event: {line}")

                        # Check duration limit
                        if duration and (time.time() - start_time) > duration:
                            print(f"\n⏰ Duration limit reached ({duration}s)")
                            break

        except KeyboardInterrupt:
            print(f"\n🛑 Interrupted by user after {event_count} events")
        except Exception as e:
            print(f"\n❌ Stream error: {e}")

    async def run_demo(self):
        """Run a complete demo: create workflow, execute it, stream results"""
        print("🚀 Running streaming demo...")
        print()

        try:
            # 1. Create a workflow
            print("1️⃣ Creating workflow...")
            workflow_config = self._load_fixture("webhook_minimal.json")
            workflow = await self._http_request("POST", "/workflows/", workflow_config)
            workflow_id = workflow["id"]
            print(f"   ✅ Created workflow: {workflow_id}")

            # 2. Execute the workflow
            print("2️⃣ Executing workflow...")
            execution_body = {
                "trigger": {"kind": "webhook"},
                "input_data": {"demo": "streaming_test", "timestamp": datetime.now().isoformat()},
                "wait": False,
            }
            execution = await self._http_request("POST", f"/workflows/{workflow_id}/execute", execution_body)
            execution_id = execution["id"]
            print(f"   ✅ Started execution: {execution_id}")

            # 3. Stream the execution
            print("3️⃣ Streaming execution events...")
            print()
            await self.stream_execution(execution_id, duration=30.0)

        except Exception as e:
            print(f"❌ Demo failed: {e}")

    async def chat(self, workflow_id: str, backend: str = "local"):
        """Interactive chat CLI that starts a paused chat workflow and resumes via messages API.
        backend: "local" or "dbos" (default: local)
        """
        print("💬 Chat CLI (type /quit to exit)")
        print(f"🧩 Workflow: {workflow_id}")
        print("=" * 80)
        try:
            # 1) Start a chat execution with no initial message to get into waiting state
            start_body = {"trigger": {"kind": "chat", "messages": []}, "wait": False}
            # Use backend-specific path to comply with project requirement
            execution = await self._http_request("POST", f"/workflows/{workflow_id}/execute/{backend}", start_body)
            execution_id = execution.get("id")
            if not execution_id:
                print(f"❌ No execution id returned: {execution}")
                return
            print(f"▶️  Started execution {execution_id}")
            # Stream until we hit waiting once, then return to input loop
            await self.stream_execution(execution_id, stop_on_waiting=True)

            print("—" * 80)

            # 2) Chat loop: alternate: send a line, then stream until waiting/completed, repeat
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in {"/quit", ":q", "/exit"}:
                    print("👋 Bye!")
                    return
                if not user_input:
                    continue

                # Resolve last known step id; prefer latest step event, fallback to waiting step id, then 'agent_1'
                step_id = self._last_step_id.get(execution_id) or self._last_waiting_step.get(execution_id) or "agent_1"

                # Start streaming first to avoid missing step events; ignore the initial waiting snapshot
                stream_task = asyncio.create_task(
                    self.stream_execution(
                        execution_id,
                        stop_on_waiting=True,
                        ignore_initial_waiting=True,
                        until_assistant=True,
                    )
                )

                # Small delay to ensure SSE connection is established before resuming
                await asyncio.sleep(0.05)

                try:
                    await self._http_request(
                        "POST",
                        f"/executions/{execution_id}/steps/{step_id}/messages",
                        {"role": "user", "content": user_input, "metadata": {"final_turn": False}},
                    )
                except Exception as e:
                    print(f"❌ Failed to send message: {e}")
                    # Cancel stream if send failed
                    stream_task.cancel()
                    with contextlib.suppress(Exception):
                        await stream_task
                    continue

                # Wait for this turn's stream to reach waiting/completed
                with contextlib.suppress(Exception):
                    await stream_task

        except KeyboardInterrupt:
            print("\n👋 Bye!")
        except Exception as e:
            print(f"❌ Chat failed: {e}")


def _parse_backend(argv: list[str]) -> str:
    try:
        if "--backend" in argv:
            idx = argv.index("--backend")
            if idx + 1 < len(argv):
                val = argv[idx + 1].strip().lower()
                if val in {"local", "dbos"}:
                    return val
    except Exception:
        pass
    return "local"


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    client = StreamingClient()
    command = sys.argv[1].lower()

    if command == "execution":
        if len(sys.argv) < 3:
            print("❌ Usage: python streaming_client.py execution <execution_id>")
            sys.exit(1)
        execution_id = sys.argv[2]
        await client.stream_execution(execution_id)

    elif command == "workflow":
        if len(sys.argv) < 3:
            print("❌ Usage: python streaming_client.py workflow <workflow_id> [execution_id]")
            sys.exit(1)
        workflow_id = sys.argv[2]
        execution_id = sys.argv[3] if len(sys.argv) > 3 else None
        await client.stream_workflow(workflow_id, execution_id)

    elif command == "demo":
        await client.run_demo()

    elif command == "chat":
        if len(sys.argv) < 3:
            print("❌ Usage: python streaming_client.py chat <workflow_id> [--backend local|dbos]")
            sys.exit(1)
        workflow_id = sys.argv[2]
        backend = _parse_backend(sys.argv)
        await client.chat(workflow_id, backend=backend)

    elif command == "chat-demo":
        # Create a chat-capable workflow from fixture and start chat
        try:
            workflow_config = client._load_fixture("chat_multi_agent.json")
            # Enable streaming in agent steps for this demo
            try:
                for step in workflow_config.get("steps", []):
                    if step.get("step_type") == "agent_execution" and isinstance(step.get("config"), dict):
                        step["config"]["stream"] = True
                        # Slightly bump tokens for a better streaming experience
                        step["config"].setdefault("max_tokens", 800)
            except Exception:
                pass
            workflow = await client._http_request("POST", "/workflows/", workflow_config)
            workflow_id = workflow.get("id")
            if not workflow_id:
                print(f"❌ Failed to create chat workflow: {workflow}")
                sys.exit(1)
            print(f"✅ Created chat workflow: {workflow_id}")
            backend = _parse_backend(sys.argv)
            await client.chat(workflow_id, backend=backend)
        except Exception as e:
            print(f"❌ chat-demo failed: {e}")
            sys.exit(1)

    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
