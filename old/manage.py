#!/usr/bin/env python3
"""
Main CLI entry point for MDJourney.
Provides a unified command-line interface for all system operations.
"""

import argparse
import sys
import logging


def main():
    """Main CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("mdjourney.cli")
    parser = argparse.ArgumentParser(
        prog="mdjourney",
        description="FAIR-compliant research data metadata automation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mdjourney setup                    # Interactive setup
  mdjourney setup --monitor-path ./data --schema-path ./schemas
  mdjourney monitor                  # Start file system monitor
  mdjourney api                      # Start API server
  mdjourney start                    # Start all services
  mdjourney start --monitor-only     # Start only monitor
  mdjourney start --api-only         # Start only API
  mdjourney start --backend-only     # Start only backend (API + Monitor)
  mdjourney start --frontend-only    # Start only frontend
  mdjourney version                  # Show version information
        """,
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", metavar="COMMAND"
    )

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Configure the system")
    setup_parser.add_argument("--monitor-path", help="Directory to monitor for changes")
    setup_parser.add_argument(
        "--schema-path", help="Directory containing custom schemas"
    )
    setup_parser.add_argument(
        "--config-path",
        default="./.fair_meta_config.yaml",
        help="Path to save configuration file",
    )

    # Monitor command
    subparsers.add_parser("monitor", help="Start file system monitor")

    # API command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="API server host")
    api_parser.add_argument("--port", type=int, default=8000, help="API server port")
    api_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    # Start command
    start_parser = subparsers.add_parser("start", help="Start all services")
    start_parser.add_argument(
        "--monitor-only", action="store_true", help="Start only the monitor service"
    )
    start_parser.add_argument(
        "--api-only", action="store_true", help="Start only the API service"
    )
    start_parser.add_argument(
        "--frontend-only", action="store_true", help="Start only the frontend service"
    )
    start_parser.add_argument(
        "--backend-only", action="store_true", help="Start only backend services (API + Monitor)"
    )
    start_parser.add_argument(
        "--api-host", default="0.0.0.0", help="API server host (default: 0.0.0.0)"
    )
    start_parser.add_argument(
        "--api-port", type=int, default=8000, help="API server port (default: 8000)"
    )
    start_parser.add_argument(
        "--no-reload", action="store_true", help="Disable API auto-reload"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    test_parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    test_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Lint command
    subparsers.add_parser("lint", help="Run linting and code formatting checks")

    # Format command
    subparsers.add_parser("format", help="Format code using black and isort")

    # Version command
    subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to appropriate command handler
    try:
        if args.command == "setup":
            from scripts.setup_config import main as setup_main

            # Convert args to match setup_config expectations
            setup_args = []
            if args.monitor_path:
                setup_args.extend(["--monitor-path", args.monitor_path])
            if args.schema_path:
                setup_args.extend(["--schema-path", args.schema_path])
            if args.config_path:
                setup_args.extend(["--config-path", args.config_path])

            # Replace sys.argv for setup_config
            old_argv = sys.argv
            sys.argv = ["setup_config"] + setup_args
            try:
                setup_main()
            finally:
                sys.argv = old_argv

        elif args.command == "monitor":
            # Initialize configuration and start the folder monitor
            from app.core.config import (
                find_config_file,
                get_monitor_path,
                initialize_config,
            )
            from app.monitors import folder_monitor as fm

            # Ensure configuration is loaded from file
            cfg = find_config_file()
            if not cfg:
                logger.error("No .fair_meta_config.yaml found. Run 'mdjourney setup' or provide a config file.")
                return 1
            if not initialize_config(str(cfg)):
                logger.error(f"Failed to initialize configuration from {cfg}.")
                return 1

            # Retrieve monitor path from loaded configuration
            try:
                monitor_path = str(get_monitor_path())
            except Exception as e:
                logger.error(f"Could not determine monitor path from configuration: {e}")
                return 1

            logger.info(f"Starting folder monitor on: {monitor_path}")
            fm.run_continuously(monitor_path=monitor_path, recursive=True)

        elif args.command == "api":
            try:
                import uvicorn
            except ImportError:
                logger.error("uvicorn not installed. Install with: pip install 'mdjourney[api]'")
                return 1

            logger.info(f"Starting API server on {args.host}:{args.port}")
            logger.info(f"Documentation: http://{args.host}:{args.port}/docs")

            uvicorn.run(
                "api.main:app",
                host=args.host,
                port=args.port,
                reload=args.reload,
                log_level="info",
            )

        elif args.command == "start":
            from scripts.process_manager import start_all_services

            # Determine which services to start
            if args.backend_only:
                monitor = True
                api = True
                frontend = False
            else:
                monitor = not args.api_only and not args.frontend_only
                api = not args.monitor_only and not args.frontend_only
                frontend = not args.monitor_only and not args.api_only

            start_all_services(
                monitor=monitor,
                api=api,
                frontend=frontend,
                api_host=args.api_host,
                api_port=args.api_port,
                api_reload=not args.no_reload,
            )

        elif args.command == "test":
            import subprocess
            import sys

            test_args = ["python", "-m", "pytest"]

            if args.unit:
                test_args.append("tests/unit/")
            elif args.integration:
                test_args.append("tests/integration/")
            else:
                test_args.append("tests/")

            if args.verbose:
                test_args.append("-v")

            result = subprocess.run(test_args)
            return result.returncode

        elif args.command == "lint":
            import subprocess
            import sys

            logger.info("Running linting checks...")

            # Run black check
            logger.info("Checking code formatting with black...")
            result = subprocess.run(["black", "--check", "."])
            if result.returncode != 0:
                logger.error("Black formatting check failed")
                return result.returncode

            # Run flake8
            logger.info("Running flake8...")
            result = subprocess.run(["flake8", "."])
            if result.returncode != 0:
                logger.error("Flake8 check failed")
                return result.returncode

            # Run mypy
            logger.info("Running mypy type checking...")
            result = subprocess.run(["mypy", "."])
            if result.returncode != 0:
                logger.error("MyPy type checking failed")
                return result.returncode

            logger.info("All linting checks passed!")
            return 0

        elif args.command == "format":
            import subprocess
            import sys

            logger.info("Formatting code...")

            # Run black
            logger.info("Running black...")
            result = subprocess.run(["black", "."])
            if result.returncode != 0:
                logger.error("Black formatting failed")
                return result.returncode

            # Run isort
            logger.info("Running isort...")
            result = subprocess.run(["isort", "."])
            if result.returncode != 0:
                logger.error("isort failed")
                return result.returncode

            logger.info("Code formatting complete!")
            return 0

        elif args.command == "version":
            from app import __description__, __version__

            logger.info(f"MDJourney {__version__}")
            logger.info(__description__)
            logger.info("Components:")
            logger.info("  - Core Application: Python package")
            logger.info("  - API Server: FastAPI")
            logger.info("  - Frontend: React + TypeScript")
            logger.info("  - Monitor: File system watcher")

        return 0

    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
