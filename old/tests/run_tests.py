#!/usr/bin/env python3
"""
Test runner for the FAIR metadata automation system.
Runs unit tests, integration tests, and regression tests.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def run_pytest_tests(test_path, verbose=False):
    """Run pytest tests for a specific path."""
    cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]

    if verbose:
        cmd.extend(["-s", "--tb=long"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def run_unit_tests(verbose=False):
    """Run all unit tests."""
    print("=" * 80)
    print("Running Unit Tests")
    print("=" * 80)

    success, stdout, stderr = run_pytest_tests("tests/unit", verbose)

    if success:
        print("✓ Unit tests passed")
        if stdout:
            print("\nTest Output:")
            print(stdout)
    else:
        print("✗ Unit tests failed")
        if stdout:
            print("\nTest Output:")
            print(stdout)
        if stderr:
            print(f"\nError Details:")
            print(stderr)

    return success


def run_integration_tests(verbose=False):
    """Run all integration tests."""
    print("=" * 80)
    print("Running Integration Tests")
    print("=" * 80)

    success, stdout, stderr = run_pytest_tests("tests/integration", verbose)

    if success:
        print("✓ Integration tests passed")
        if stdout:
            print("\nTest Output:")
            print(stdout)
    else:
        print("✗ Integration tests failed")
        if stdout:
            print("\nTest Output:")
            print(stdout)
        if stderr:
            print(f"\nError Details:")
            print(stderr)

    return success


def run_regression_tests(verbose=False):
    """Run all regression tests."""
    print("=" * 80)
    print("Running Regression Tests")
    print("=" * 80)

    success, stdout, stderr = run_pytest_tests("tests/regression", verbose)

    if success:
        print("✓ Regression tests passed")
        if stdout:
            print("\nTest Output:")
            print(stdout)
    else:
        print("✗ Regression tests failed")
        if stdout:
            print("\nTest Output:")
            print(stdout)
        if stderr:
            print(f"\nError Details:")
            print(stderr)

    return success


def run_all_tests(verbose=False):
    """Run all tests."""
    print("=" * 80)
    print("Running All Tests")
    print("=" * 80)

    unit_success = run_unit_tests(verbose)
    integration_success = run_integration_tests(verbose)
    regression_success = run_regression_tests(verbose)

    all_success = unit_success and integration_success and regression_success

    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Unit Tests: {'✓ PASSED' if unit_success else '✗ FAILED'}")
    print(f"Integration Tests: {'✓ PASSED' if integration_success else '✗ FAILED'}")
    print(f"Regression Tests: {'✓ PASSED' if regression_success else '✗ FAILED'}")
    print(f"Overall: {'✓ ALL TESTS PASSED' if all_success else '✗ SOME TESTS FAILED'}")

    return all_success


def main():
    """Main test runner function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run tests for the FAIR metadata automation system"
    )
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--regression", action="store_true", help="Run only regression tests"
    )
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Default to running all tests if no specific test type is specified
    if not any([args.unit, args.integration, args.regression, args.all]):
        args.all = True

    success = True

    if args.unit:
        success = run_unit_tests(args.verbose)
    elif args.integration:
        success = run_integration_tests(args.verbose)
    elif args.regression:
        success = run_regression_tests(args.verbose)
    elif args.all:
        success = run_all_tests(args.verbose)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
