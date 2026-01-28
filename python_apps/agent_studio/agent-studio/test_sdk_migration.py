"""
Test script to verify SDK migration with adapter layer

This script tests that the migrated endpoint works correctly and returns
Agent Studio format responses.
"""

import asyncio
import pytest
from uuid import uuid4

# Test imports
from adapters import ExecutionAdapter

# SDK imports

# Database


@pytest.mark.asyncio
async def test_adapter_conversion():
    """Test that adapters correctly convert between formats"""
    print("\n" + "=" * 60)
    print("TEST 1: Adapter Conversion")
    print("=" * 60)

    # Create a mock SDK execution
    sdk_execution = {
        "id": str(uuid4()),
        "workflow_id": str(uuid4()),
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
        "current_step_id": "step_1",
    }

    print("\n📥 SDK Format:")
    print(f"  - id: {sdk_execution['id']}")
    print(f"  - status: {sdk_execution['status']}")
    print(f"  - current_step_id: {sdk_execution['current_step_id']}")

    # Adapt to Agent Studio format
    as_response = ExecutionAdapter.adapt_status_response(sdk_execution)

    print("\n📤 Agent Studio Format:")
    print(f"  - execution_id: {as_response['execution_id']}")
    print(f"  - status: {as_response['status']}")
    print(f"  - current_step: {as_response.get('current_step')}")

    # Verify mappings
    assert as_response["execution_id"] == sdk_execution["id"], "ID mapping failed"
    assert as_response["status"] == "queued", "Status mapping failed (pending -> queued)"
    assert as_response.get("current_step") == "step_1", "Current step mapping failed"

    print("\n✅ Adapter conversion test PASSED")
    return True


@pytest.mark.asyncio
async def test_status_mapping():
    """Test all status value mappings"""
    print("\n" + "=" * 60)
    print("TEST 2: Status Mapping")
    print("=" * 60)

    status_tests = [
        ("pending", "queued"),
        ("running", "running"),
        ("completed", "completed"),
        ("failed", "failed"),
        ("cancelled", "cancelled"),
    ]

    for sdk_status, expected_as_status in status_tests:
        sdk_execution = {
            "id": str(uuid4()),
            "workflow_id": str(uuid4()),
            "status": sdk_status,
        }

        as_response = ExecutionAdapter.adapt_status_response(sdk_execution)

        print(f"  {sdk_status:12} -> {as_response['status']:12} ", end="")

        if as_response["status"] == expected_as_status:
            print("✅")
        else:
            print(f"❌ (expected {expected_as_status})")
            return False

    print("\n✅ Status mapping test PASSED")
    return True


@pytest.mark.asyncio
async def test_request_adaptation():
    """Test request format adaptation"""
    print("\n" + "=" * 60)
    print("TEST 3: Request Adaptation")
    print("=" * 60)

    # Agent Studio execution request
    as_request = {
        "user_message": "Hello, world!",
        "session_id": "session_123",
        "user_id": "user_456",
        "attachments": [{"file_name": "doc.pdf", "file_path": "/uploads/doc.pdf"}],
    }

    print("\n📥 Agent Studio Request:")
    print(f"  - user_message: {as_request['user_message']}")
    print(f"  - session_id: {as_request['session_id']}")
    print(f"  - attachments: {len(as_request['attachments'])} file(s)")

    # Adapt to SDK format
    from adapters import RequestAdapter

    sdk_request = RequestAdapter.adapt_workflow_execute_request(as_request)

    print("\n📤 SDK Request:")
    print(f"  - input.message: {sdk_request['input']['message']}")
    print(f"  - user_context.session_id: {sdk_request['user_context']['session_id']}")
    print(f"  - input.attachments: {len(sdk_request['input']['attachments'])} file(s)")

    # Verify
    assert sdk_request["input"]["message"] == "Hello, world!"
    assert sdk_request["user_context"]["session_id"] == "session_123"
    assert len(sdk_request["input"]["attachments"]) == 1

    print("\n✅ Request adaptation test PASSED")
    return True


@pytest.mark.asyncio
async def test_workflow_structure_conversion():
    """Test workflow structure conversion (agents -> steps)"""
    print("\n" + "=" * 60)
    print("TEST 4: Workflow Structure Conversion")
    print("=" * 60)

    # Agent Studio workflow format
    as_workflow = {
        "name": "Test Workflow",
        "configuration": {
            "agents": [
                {
                    "agent_id": "agent_1",
                    "name": "Analyzer",
                    "config": {"system_prompt": "You are an analyzer"},
                }
            ],
            "connections": [
                {
                    "source_agent_id": "agent_1",
                    "target_agent_id": "agent_2",
                }
            ],
        },
    }

    print("\n📥 Agent Studio Workflow:")
    print(f"  - agents: {len(as_workflow['configuration']['agents'])}")
    print(f"  - connections: {len(as_workflow['configuration']['connections'])}")

    # Adapt to SDK format
    from adapters import RequestAdapter

    sdk_workflow = RequestAdapter.adapt_workflow_create_request(as_workflow)

    print("\n📤 SDK Workflow:")
    print(f"  - steps: {len(sdk_workflow['configuration']['steps'])}")
    print(f"  - step_type: {sdk_workflow['configuration']['steps'][0]['step_type']}")

    # Verify
    assert len(sdk_workflow["configuration"]["steps"]) == 1
    assert sdk_workflow["configuration"]["steps"][0]["step_type"] == "agent_execution"

    print("\n✅ Workflow structure conversion test PASSED")
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 SDK MIGRATION ADAPTER TESTS")
    print("=" * 60)

    tests = [
        ("Adapter Conversion", test_adapter_conversion),
        ("Status Mapping", test_status_mapping),
        ("Request Adaptation", test_request_adaptation),
        ("Workflow Structure", test_workflow_structure_conversion),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:30} {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests PASSED! SDK migration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
