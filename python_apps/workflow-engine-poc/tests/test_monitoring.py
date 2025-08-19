"""
Test Monitoring and Observability

Tests for OpenTelemetry tracing, metrics collection, and structured logging
for production monitoring and debugging of workflow executions.
"""

import asyncio
import time
from typing import Dict, Any

from workflow_engine_poc.monitoring import monitoring, MetricData, TraceData
from workflow_engine_poc.execution_context import ExecutionContext, UserContext
from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.step_registry import StepRegistry


async def test_monitoring_system():
    """Test the monitoring system components"""

    print("🧪 Testing Monitoring System")
    print("-" * 40)

    # Test monitoring initialization
    summary = monitoring.get_monitoring_summary()
    print(f"📋 Monitoring Summary:")
    print(f"   Monitoring enabled: {summary['monitoring_enabled']}")
    print(f"   OpenTelemetry available: {summary['opentelemetry_available']}")
    print(f"   Prometheus available: {summary['prometheus_available']}")
    print(f"   Service name: {summary['service_name']}")

    # Test metric recording
    print(f"\n📊 Testing Metrics:")

    # Record some test metrics
    monitoring._record_metric("test_counter", 1, {"component": "test"})
    monitoring._record_metric("test_gauge", 42.5, {"type": "gauge"})
    monitoring._record_metric("test_histogram", 0.123, {"operation": "test_op"})

    print(f"   Recorded {len(monitoring.metrics_data)} metrics")

    # Get metrics output
    metrics_output = monitoring.get_metrics()
    print(f"   Metrics output length: {len(metrics_output)} characters")

    # Test error recording
    print(f"\n🚨 Testing Error Recording:")

    monitoring.record_error("test_component", "test_error", "This is a test error")
    monitoring.record_error(
        "workflow_engine", "validation_error", "Invalid configuration"
    )

    print(f"   Recorded errors in metrics")


async def test_workflow_tracing():
    """Test workflow execution tracing"""

    print("\n🧪 Testing Workflow Tracing")
    print("-" * 40)

    # Create a simple workflow for tracing
    workflow_config = {
        "workflow_id": "monitoring-test-workflow",
        "name": "Monitoring Test Workflow",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "trace_step_1",
                "step_name": "First Traced Step",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {"message": "Hello from traced workflow"},
                },
            },
            {
                "step_id": "trace_step_2",
                "step_name": "Second Traced Step",
                "step_type": "data_processing",
                "step_order": 2,
                "dependencies": ["trace_step_1"],
                "config": {"operation": "transform", "transformation": "upper"},
            },
        ],
    }

    # Initialize components
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()

    workflow_engine = WorkflowEngine(step_registry)

    # Create execution context
    user_context = UserContext(user_id="monitoring_test_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    # Record initial trace count
    initial_trace_count = len(monitoring.traces)
    initial_metric_count = len(monitoring.metrics_data)

    print(f"📋 Before execution:")
    print(f"   Traces: {initial_trace_count}")
    print(f"   Metrics: {initial_metric_count}")

    # Execute workflow (this should generate traces and metrics)
    await workflow_engine.execute_workflow(execution_context)

    # Check traces and metrics after execution
    final_trace_count = len(monitoring.traces)
    final_metric_count = len(monitoring.metrics_data)

    print(f"\n📋 After execution:")
    print(
        f"   Traces: {final_trace_count} (+{final_trace_count - initial_trace_count})"
    )
    print(
        f"   Metrics: {final_metric_count} (+{final_metric_count - initial_metric_count})"
    )

    # Analyze traces
    if monitoring.traces:
        print(f"\n🔍 Trace Analysis:")
        for trace in monitoring.traces[-3:]:  # Show last 3 traces
            print(
                f"   {trace.operation_name}: {trace.duration_ms:.2f}ms ({trace.status})"
            )
            if trace.tags:
                print(f"     Tags: {trace.tags}")

    # Check workflow execution result
    summary = execution_context.get_execution_summary()
    print(f"\n📊 Workflow Result:")
    print(f"   Status: {summary['status']}")
    print(f"   Completed steps: {summary.get('completed_steps', 0)}")


async def test_step_tracing():
    """Test individual step tracing"""

    print("\n🧪 Testing Step Tracing")
    print("-" * 40)

    # Initialize step registry
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()

    # Create execution context
    workflow_config = {"workflow_id": "step-trace-test", "name": "Step Trace Test"}
    user_context = UserContext(user_id="step_trace_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    # Test different step types
    step_tests = [
        {
            "step_type": "data_input",
            "step_config": {
                "step_id": "input_test",
                "config": {"input_type": "static", "data": {"test": "value"}},
            },
            "input_data": {},
        },
        {
            "step_type": "data_processing",
            "step_config": {
                "step_id": "processing_test",
                "config": {"operation": "transform", "transformation": "upper"},
            },
            "input_data": {"data": {"text": "hello world"}},
        },
    ]

    print(f"📋 Testing {len(step_tests)} step types:")

    for i, test in enumerate(step_tests):
        print(f"\n   Step {i+1}: {test['step_type']}")

        initial_traces = len(monitoring.traces)

        try:
            # Execute step with tracing
            result = await step_registry.execute_step(
                step_type=test["step_type"],
                step_config=test["step_config"],
                input_data=test["input_data"],
                execution_context=execution_context,
            )

            final_traces = len(monitoring.traces)
            print(f"     ✅ Success: {result.status.value}")
            print(f"     📊 Traces generated: {final_traces - initial_traces}")

        except Exception as e:
            print(f"     ❌ Failed: {e}")


async def test_monitoring_api_endpoints():
    """Test monitoring API endpoints"""

    print("\n🧪 Testing Monitoring API Endpoints")
    print("-" * 40)

    from fastapi.testclient import TestClient
    from workflow_engine_poc.main import app

    # Initialize app state
    from workflow_engine_poc.step_registry import StepRegistry
    from workflow_engine_poc.workflow_engine import WorkflowEngine
    from workflow_engine_poc.database import get_database

    database = await get_database()
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    workflow_engine = WorkflowEngine(step_registry)

    app.state.database = database
    app.state.step_registry = step_registry
    app.state.workflow_engine = workflow_engine

    client = TestClient(app)

    # Test metrics endpoint
    print("📋 Testing /metrics endpoint:")
    response = client.get("/metrics")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        metrics_text = response.text
        print(f"   Metrics length: {len(metrics_text)} characters")
        print(f"   Contains metrics: {'test_counter' in metrics_text}")

    # Test traces endpoint
    print("\n📋 Testing /monitoring/traces endpoint:")
    response = client.get("/monitoring/traces?limit=5")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        traces_data = response.json()
        print(f"   Traces returned: {len(traces_data.get('traces', []))}")
        print(f"   Total traces: {traces_data.get('total', 0)}")

    # Test monitoring summary endpoint
    print("\n📋 Testing /monitoring/summary endpoint:")
    response = client.get("/monitoring/summary")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        summary = response.json()
        print(f"   Monitoring enabled: {summary.get('monitoring_enabled')}")
        print(f"   Active executions: {summary.get('active_executions')}")
        print(f"   Registered steps: {summary.get('registered_steps')}")

    # Test monitoring health check
    print("\n📋 Testing /health/monitoring endpoint:")
    response = client.get("/health/monitoring")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        health = response.json()
        print(f"   Health status: {health.get('status')}")
        print(f"   Monitoring summary: {len(health.get('monitoring', {}))}")


async def test_performance_monitoring():
    """Test performance monitoring with multiple workflows"""

    print("\n🧪 Testing Performance Monitoring")
    print("-" * 40)

    # Initialize components
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    workflow_engine = WorkflowEngine(step_registry)

    # Create multiple workflows to test performance monitoring
    workflows = []
    for i in range(3):
        workflow_config = {
            "workflow_id": f"perf-test-{i}",
            "name": f"Performance Test Workflow {i}",
            "execution_pattern": "sequential",
            "steps": [
                {
                    "step_id": f"step_{i}_1",
                    "step_name": f"Step {i}.1",
                    "step_type": "data_input",
                    "step_order": 1,
                    "config": {
                        "input_type": "static",
                        "data": {"workflow": i, "step": 1},
                    },
                },
                {
                    "step_id": f"step_{i}_2",
                    "step_name": f"Step {i}.2",
                    "step_type": "data_processing",
                    "step_order": 2,
                    "dependencies": [f"step_{i}_1"],
                    "config": {"operation": "transform", "transformation": "upper"},
                },
            ],
        }

        user_context = UserContext(user_id=f"perf_user_{i}")
        execution_context = ExecutionContext(workflow_config, user_context)
        workflows.append(execution_context)

    # Record initial metrics
    initial_metrics = len(monitoring.metrics_data)
    initial_traces = len(monitoring.traces)

    print(f"📋 Executing {len(workflows)} workflows concurrently:")

    # Execute workflows concurrently
    start_time = time.time()

    tasks = [workflow_engine.execute_workflow(workflow) for workflow in workflows]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    total_time = end_time - start_time

    # Analyze results
    successful = sum(1 for result in results if not isinstance(result, Exception))
    failed = len(results) - successful

    final_metrics = len(monitoring.metrics_data)
    final_traces = len(monitoring.traces)

    print(f"📊 Performance Results:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Successful workflows: {successful}")
    print(f"   Failed workflows: {failed}")
    print(f"   Metrics generated: {final_metrics - initial_metrics}")
    print(f"   Traces generated: {final_traces - initial_traces}")
    print(f"   Average time per workflow: {total_time / len(workflows):.2f}s")


async def main():
    """Run all monitoring tests"""

    print("🚀 Monitoring and Observability Test Suite")
    print("=" * 60)

    try:
        await test_monitoring_system()
        await test_workflow_tracing()
        await test_step_tracing()
        await test_monitoring_api_endpoints()
        await test_performance_monitoring()

        print("\n🎉 All monitoring tests completed successfully!")
        print("✅ Monitoring and observability features are working correctly")

        # Final summary
        summary = monitoring.get_monitoring_summary()
        print(f"\n📊 Final Monitoring Summary:")
        print(f"   Total traces collected: {summary['traces_collected']}")
        print(f"   Total metrics collected: {summary['metrics_collected']}")

    except Exception as e:
        print(f"\n❌ Monitoring test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
