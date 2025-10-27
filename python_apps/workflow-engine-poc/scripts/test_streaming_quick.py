#!/usr/bin/env python3
"""
Quick streaming test script to validate streaming functionality.

This script creates a workflow, executes it, and streams the results
to verify everything is working correctly.
"""

import asyncio
import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8006"
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "e2e" / "fixtures"


async def quick_test():
    """Run a quick streaming test"""
    print("🧪 Quick Streaming Test")
    print("=" * 50)

    try:
        # Check server health
        print("1. Checking server health...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                print(f"❌ Server not healthy: {response.status_code}")
                return False
        print("   ✅ Server is healthy")

        # Load fixture
        print("2. Loading test workflow...")
        fixture_path = FIXTURES_DIR / "webhook_minimal.json"
        with open(fixture_path) as f:
            workflow_config = json.load(f)
        print("   ✅ Loaded webhook_minimal.json")

        # Create workflow
        print("3. Creating workflow...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{BASE_URL}/workflows/", json=workflow_config)
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to create workflow: {response.status_code} {response.text}")
                return False
            workflow = response.json()
            workflow_id = workflow["id"]
        print(f"   ✅ Created workflow: {workflow_id}")

        # Execute workflow
        print("4. Executing workflow...")
        execution_body = {"trigger": {"kind": "webhook"}, "input_data": {"test": "quick_streaming_test"}, "wait": False}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{BASE_URL}/workflows/{workflow_id}/execute", json=execution_body)
            if response.status_code != 200:
                print(f"❌ Failed to execute workflow: {response.status_code} {response.text}")
                return False
            execution = response.json()
            execution_id = execution["id"]
        print(f"   ✅ Started execution: {execution_id}")

        # Test execution streaming
        print("5. Testing execution streaming...")
        events_received = 0
        start_time = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("GET", f"{BASE_URL}/executions/{execution_id}/stream") as response:
                if response.status_code != 200:
                    print(f"❌ Execution stream failed: {response.status_code}")
                    return False

                async for chunk in response.aiter_text():
                    if chunk.strip():
                        lines = chunk.strip().split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                try:
                                    event = json.loads(line[6:])
                                    events_received += 1
                                    event_type = event.get("type", "unknown")
                                    print(f"   📡 Event {events_received}: {event_type}")

                                    # Stop after getting some events or completion
                                    if event_type == "complete" or events_received >= 5:
                                        break
                                except json.JSONDecodeError:
                                    print(f"   ⚠️  Malformed event: {line}")

                    # Timeout after 15 seconds
                    if time.time() - start_time > 15:
                        break

                    if events_received > 0:
                        break

        if events_received == 0:
            print("   ❌ No events received from execution stream")
            return False
        print(f"   ✅ Received {events_received} events from execution stream")

        # Test workflow streaming
        print("6. Testing workflow streaming...")
        events_received = 0
        start_time = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("GET", f"{BASE_URL}/workflows/{workflow_id}/stream") as response:
                if response.status_code != 200:
                    print(f"❌ Workflow stream failed: {response.status_code}")
                    return False

                async for chunk in response.aiter_text():
                    if chunk.strip():
                        lines = chunk.strip().split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                try:
                                    event = json.loads(line[6:])
                                    events_received += 1
                                    event_type = event.get("type", "unknown")
                                    print(f"   📡 Event {events_received}: {event_type}")

                                    # Stop after getting some events or completion
                                    if event_type == "complete" or events_received >= 3:
                                        break
                                except json.JSONDecodeError:
                                    print(f"   ⚠️  Malformed event: {line}")

                    # Timeout after 10 seconds
                    if time.time() - start_time > 10:
                        break

                    if events_received > 0:
                        break

        if events_received == 0:
            print("   ❌ No events received from workflow stream")
            return False
        print(f"   ✅ Received {events_received} events from workflow stream")

        print("\n🎉 All streaming tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


async def main():
    success = await quick_test()
    if not success:
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
