#!/usr/bin/env python3
"""
Build script for MDJourney package.
Handles frontend build integration and package preparation.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    if cwd:
        print(f"  in directory: {cwd}")

    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)

    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)

    return result


def build_frontend():
    """Build the frontend for production."""
    frontend_dir = Path("frontend")

    if not frontend_dir.exists():
        print("Warning: Frontend directory not found, skipping frontend build")
        return

    print("Building frontend...")

    # Install dependencies
    run_command("npm ci", cwd=frontend_dir)

    # Run build
    run_command("npm run build", cwd=frontend_dir)

    # Verify build output
    dist_dir = frontend_dir / "dist"
    if not dist_dir.exists():
        raise RuntimeError("Frontend build failed - dist directory not found")

    print(f"Frontend built successfully in {dist_dir}")


def clean_build_artifacts():
    """Clean existing build artifacts."""
    print("Cleaning build artifacts...")

    # Directories to clean
    dirs_to_clean = [
        "build/",
        "dist/",
        "*.egg-info/",
        "frontend/dist/",
        "__pycache__/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
    ]

    for pattern in dirs_to_clean:
        if "*" in pattern:
            # Use shell glob for wildcard patterns
            run_command(f"rm -rf {pattern}", check=False)
        else:
            path = Path(pattern)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"Removed: {path}")


def check_package_health():
    """Run package health checks."""
    print("Running package health checks...")

    # Check if pyproject.toml is valid
    try:
        import tomli

        with open("pyproject.toml", "rb") as f:
            tomli.load(f)
        print("✓ pyproject.toml is valid")
    except ImportError:
        print("Warning: tomli not available, skipping pyproject.toml validation")
    except Exception as e:
        print(f"✗ pyproject.toml validation failed: {e}")
        return False

    # Check manifest
    try:
        run_command("check-manifest --ignore frontend/node_modules,frontend/dist")
        print("✓ MANIFEST.in is valid")
    except subprocess.CalledProcessError:
        print("Warning: check-manifest failed or not installed")
    except FileNotFoundError:
        print(
            "Warning: check-manifest not found, install with: pip install check-manifest"
        )

    return True


def build_package():
    """Build the Python package."""
    print("Building Python package...")

    # Install build dependencies
    run_command("pip install -U build twine check-manifest")

    # Build the package
    run_command("python -m build")

    # Check the package
    run_command("twine check dist/*")

    print("Package built successfully!")

    # List built files
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("\nBuilt files:")
        for file in sorted(dist_dir.iterdir()):
            print(f"  {file.name}")


def main():
    """Main build function."""
    print("=== MDJourney Package Build ===")

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    try:
        # Clean previous builds
        clean_build_artifacts()

        # Build frontend
        build_frontend()

        # Check package health
        if not check_package_health():
            print("Package health check failed")
            return 1

        # Build package
        build_package()

        print("\n✓ Build completed successfully!")
        print("\nNext steps:")
        print("  - Test the package: pip install dist/*.whl")
        print("  - Upload to test PyPI: twine upload --repository testpypi dist/*")
        print("  - Upload to PyPI: twine upload dist/*")

        return 0

    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
