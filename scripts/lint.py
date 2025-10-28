#!/usr/bin/env python3
"""
Comprehensive linting script for the FAIR metadata automation system.
Runs multiple linters to ensure code quality and consistency.
"""

import os
import subprocess
import sys
from typing import Dict, List


class LinterRunner:
    """Manages running multiple linters on the codebase."""

    def __init__(self) -> None:
        """Initialize the linter runner."""
        self.results: Dict[str, bool] = {}
        self.errors: Dict[str, List[str]] = {}

    def run_command(self, cmd: List[str], name: str) -> bool:
        """Run a command and capture its output."""
        print(f"\n{'='*60}")
        print(f"Running {name}...")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=os.getcwd()
            )

            if result.stdout:
                print("Output:")
                print(result.stdout)

            if result.stderr:
                print("Errors/Warnings:")
                print(result.stderr)

            success = result.returncode == 0
            self.results[name] = success

            if not success:
                self.errors[name] = result.stderr.split("\n") if result.stderr else []

            status = "✓ PASSED" if success else "✗ FAILED"
            print(f"\n{name}: {status}")

            return success

        except Exception as e:
            print(f"Error running {name}: {e}")
            self.results[name] = False
            self.errors[name] = [str(e)]
            return False

    def run_black(self) -> bool:
        """Run Black code formatter."""
        return self.run_command(["black", "--check", "."], "Black (Code Formatting)")

    def run_isort(self) -> bool:
        """Run isort import sorter."""
        return self.run_command(
            ["isort", "--check-only", "."], "isort (Import Sorting)"
        )

    def run_flake8(self) -> bool:
        """Run flake8 style checker."""
        return self.run_command(["flake8", "."], "Flake8 (Style & Complexity)")

    def run_mypy(self) -> bool:
        """Run mypy type checker."""
        return self.run_command(["mypy", "."], "MyPy (Type Checking)")

    def run_pylint(self) -> bool:
        """Run pylint code analyzer."""
        return self.run_command(["pylint", "*.py"], "PyLint (Code Analysis)")

    def run_bandit(self) -> bool:
        """Run bandit security linter."""
        return self.run_command(["bandit", "-r", "."], "Bandit (Security)")

    def run_all(self) -> bool:
        """Run all linters."""
        print("🔍 Starting comprehensive code linting...")
        print(f"Working directory: {os.getcwd()}")

        # Run all linters
        linters = [
            self.run_black,
            self.run_isort,
            self.run_flake8,
            self.run_mypy,
            self.run_pylint,
            self.run_bandit,
        ]

        all_passed = True
        for linter in linters:
            if not linter():
                all_passed = False

        # Print summary
        self.print_summary()

        return all_passed

    def print_summary(self) -> None:
        """Print a summary of all linting results."""
        print(f"\n{'='*80}")
        print("LINTING SUMMARY")
        print(f"{'='*80}")

        passed_count = sum(1 for passed in self.results.values() if passed)
        total_count = len(self.results)

        for name, passed in self.results.items():
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{name:<25} {status}")

        print(f"\nOverall: {passed_count}/{total_count} linters passed")

        if passed_count < total_count:
            print(f"\n{'='*80}")
            print("ERROR DETAILS")
            print(f"{'='*80}")

            for name, errors in self.errors.items():
                if errors:
                    print(f"\n{name}:")
                    for error in errors[:5]:  # Show first 5 errors
                        print(f"  {error}")
                    if len(errors) > 5:
                        print(f"  ... and {len(errors) - 5} more errors")


def install_dev_dependencies() -> None:
    """Install development dependencies if not already installed."""
    try:
        # Check if key linters are installed
        subprocess.run(["black", "--version"], capture_output=True, check=True)
        print("✓ Development dependencies already installed")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing development dependencies...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "black",
                    "flake8",
                    "isort",
                    "mypy",
                    "pylint",
                    "bandit",
                ],
                check=True,
            )
            print("✓ Development dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install development dependencies: {e}")
            sys.exit(1)


def main() -> None:
    """Main function to run the linting process."""
    import argparse

    parser = argparse.ArgumentParser(description="Run comprehensive code linting")
    parser.add_argument("--fix", action="store_true", help="Auto-fix formatting issues")
    parser.add_argument(
        "--install-deps", action="store_true", help="Install development dependencies"
    )

    args = parser.parse_args()

    if args.install_deps:
        install_dev_dependencies()
        return

    if args.fix:
        print("🔧 Auto-fixing formatting issues...")
        subprocess.run(["black", "."], check=True)
        subprocess.run(["isort", "."], check=True)
        print("✓ Formatting fixes applied")

    # Run linting
    runner = LinterRunner()
    success = runner.run_all()

    if not success:
        print("\n❌ Some linters failed. Please fix the issues above.")
        sys.exit(1)
    else:
        print("\n✅ All linters passed!")


if __name__ == "__main__":
    main()
