#!/usr/bin/env python3
"""
Agent Studio Test Runner

Comprehensive test runner for the Agent Studio application.
Provides organized test execution with detailed reporting.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    print(f"\n{'=' * 60}")
    if description:
        print(f"🧪 {description}")
        print("=" * 60)

    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0, result
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False, None


def run_analytics_tests():
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/functional/test_analytics_endpoints.py",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, "Analytics Endpoint Tests")


def run_demo_tests():
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/functional/test_demo_endpoints.py",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, "Demo Endpoint Tests")


def run_tool_tests():
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/unit/test_tool_storage.py",
        "tests/integration/test_tool_registry.py",
        "tests/functional/test_tool_endpoints.py",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, "Tool Storage Tests")


def run_functional_tests():
    cmd = ["python", "-m", "pytest", "tests/functional/", "-v", "--tb=short"]
    return run_command(cmd, "All Functional Tests")


def run_integration_tests():
    cmd = ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
    return run_command(cmd, "All Integration Tests")


def run_unit_tests():
    cmd = ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
    return run_command(cmd, "All Unit Tests")


def run_all_tests():
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
    return run_command(cmd, "All Tests")


def run_tests_with_coverage():
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
    ]
    return run_command(cmd, "All Tests with Coverage")


def run_quick_tests():
    print("\n🚀 Running Quick Test Suite (Critical Tests Only)")
    print("=" * 60)

    success1, _ = run_analytics_tests()
    success2 = run_tool_tests()

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/unit/test_demo_service.py::TestDemoInitializationService::test_service_initialization",
        "-v",
    ]
    success3, _ = run_command(cmd, "Key Unit Test")

    return success1 and success2 and success3


def main():
    parser = argparse.ArgumentParser(description="Agent Studio Test Runner")
    parser.add_argument("--analytics", action="store_true", help="Run analytics tests only")
    parser.add_argument("--demo", action="store_true", help="Run demo tests only")
    parser.add_argument("--tools", action="store_true", help="Run tool storage tests only")
    parser.add_argument("--functional", action="store_true", help="Run functional tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--coverage", action="store_true", help="Run all tests with coverage")
    parser.add_argument("--quick", action="store_true", help="Run quick test suite")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    args = parser.parse_args()

    print("🧪 Agent Studio Test Runner")
    print("=" * 60)
    print("Available test categories:")
    print("  📊 Analytics Tests - API endpoint tests for analytics")
    print("  🎭 Demo Tests - API endpoint tests for demo functionality")
    print("  🔧 Tool Tests - Tool storage, registry, and API tests")
    print("  🧪 Functional Tests - All API and feature tests")
    print("  🔗 Integration Tests - Cross-component integration tests")
    print("  ⚙️  Unit Tests - Individual component tests")
    print("  📈 Coverage Tests - All tests with coverage reporting")
    print("  🚀 Quick Tests - Critical tests only")

    success = True

    if args.analytics:
        success, _ = run_analytics_tests()
    elif args.demo:
        success, _ = run_demo_tests()
    elif args.tools:
        success = run_tool_tests()
    elif args.functional:
        success, _ = run_functional_tests()
    elif args.integration:
        success, _ = run_integration_tests()
    elif args.unit:
        success, _ = run_unit_tests()
    elif args.coverage:
        success, _ = run_tests_with_coverage()
    elif args.quick:
        success = run_quick_tests()
    else:
        success, _ = run_all_tests()

    print("\n" + "=" * 60)
    if success:
        print("🎉 Tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
