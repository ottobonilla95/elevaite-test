import subprocess
import sys
from pathlib import Path


class TestMfaSuite:
    """
    Comprehensive test suite for MFA 24-hour bypass functionality.

    This class organizes all MFA-related tests into logical categories
    that can be run individually or as a complete suite.
    """

    def test_device_fingerprinting(self):
        """Run device fingerprinting unit tests."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/test_device_fingerprint.py",
                "-v",
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        print("Device Fingerprinting Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert (
            result.returncode == 0
        ), f"Device fingerprinting tests failed: {result.stderr}"

    def test_mfa_device_service(self):
        """Run MFA device service unit tests."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/test_mfa_device_service.py",
                "-v",
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        print("MFA Device Service Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert (
            result.returncode == 0
        ), f"MFA device service tests failed: {result.stderr}"

    def test_cleanup_tasks(self):
        """Run cleanup tasks unit tests."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/test_cleanup_tasks.py", "-v"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        print("Cleanup Tasks Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert result.returncode == 0, f"Cleanup tasks tests failed: {result.stderr}"

    def test_mfa_integration(self):
        """Run MFA integration tests."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration/test_mfa_device_bypass.py",
                "-v",
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        print("MFA Integration Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert result.returncode == 0, f"MFA integration tests failed: {result.stderr}"

    def test_admin_endpoints(self):
        """Run MFA admin endpoints tests."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration/test_mfa_admin_endpoints.py",
                "-v",
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        print("MFA Admin Endpoints Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert (
            result.returncode == 0
        ), f"MFA admin endpoints tests failed: {result.stderr}"

    def test_security_improvements(self):
        """Run security improvements tests."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration/test_security_improvements.py",
                "-v",
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        print("Security Improvements Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        assert (
            result.returncode == 0
        ), f"Security improvements tests failed: {result.stderr}"


def run_all_mfa_tests():
    """
    Run all MFA-related tests in sequence.

    This function can be called directly to run the complete test suite.
    """
    test_files = [
        "tests/unit/test_device_fingerprint.py",
        "tests/unit/test_mfa_device_service.py",
        "tests/unit/test_cleanup_tasks.py",
        "tests/integration/test_mfa_device_bypass.py",
        "tests/integration/test_mfa_admin_endpoints.py",
        "tests/integration/test_security_improvements.py",
    ]

    print("🔐 Running MFA 24-Hour Bypass Test Suite")
    print("=" * 50)

    failed_tests = []

    for test_file in test_files:
        print(f"\n📋 Running {test_file}...")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode != 0:
            failed_tests.append(test_file)
            print(f"❌ {test_file} FAILED")
        else:
            print(f"✅ {test_file} PASSED")

    print("\n" + "=" * 50)
    print("📊 Test Suite Summary")
    print("=" * 50)

    if failed_tests:
        print(f"❌ {len(failed_tests)} test file(s) failed:")
        for test_file in failed_tests:
            print(f"   - {test_file}")
        print(f"✅ {len(test_files) - len(failed_tests)} test file(s) passed")
        return False
    else:
        print(f"✅ All {len(test_files)} test files passed!")
        return True


def run_mfa_tests_with_coverage():
    """
    Run all MFA tests with coverage reporting.
    """
    print("🔐 Running MFA 24-Hour Bypass Test Suite with Coverage")
    print("=" * 60)

    coverage_modules = [
        "app.services.mfa_device_service",
        "app.core.device_fingerprint",
        "app.tasks.cleanup_tasks",
        "app.routers.auth",  # For the new endpoints
    ]

    test_files = [
        "tests/unit/test_device_fingerprint.py",
        "tests/unit/test_mfa_device_service.py",
        "tests/unit/test_cleanup_tasks.py",
        "tests/integration/test_mfa_device_bypass.py",
        "tests/integration/test_mfa_admin_endpoints.py",
        "tests/integration/test_security_improvements.py",
    ]

    # Build coverage command
    coverage_args = []
    for module in coverage_modules:
        coverage_args.extend(["--cov", module])

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *test_files,
        *coverage_args,
        "--cov-report",
        "term-missing",
        "--cov-report",
        "html:htmlcov/mfa_coverage",
        "-v",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    if result.returncode == 0:
        print("\n✅ All tests passed with coverage!")
        print("📊 Coverage report generated in htmlcov/mfa_coverage/")
    else:
        print("\n❌ Some tests failed!")

    return result.returncode == 0


if __name__ == "__main__":
    """
    Run the test suite when this file is executed directly.

    Usage:
        python tests/test_mfa_suite.py                    # Run all tests
        python tests/test_mfa_suite.py --coverage         # Run with coverage
    """
    import argparse

    parser = argparse.ArgumentParser(description="MFA 24-Hour Bypass Test Suite")
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage reporting"
    )

    args = parser.parse_args()

    if args.coverage:
        success = run_mfa_tests_with_coverage()
    else:
        success = run_all_mfa_tests()

    sys.exit(0 if success else 1)
