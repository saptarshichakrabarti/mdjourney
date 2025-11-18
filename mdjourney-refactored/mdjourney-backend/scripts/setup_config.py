#!/usr/bin/env python3
"""
Setup tool for the FAIR metadata automation system.
Provides both interactive and non-interactive configuration setup.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config_manager import ConfigManager


def validate_directory_path(path_str: str) -> bool:
    """
    Validate that a path string represents a valid directory.

    Args:
        path_str: Path string to validate.

    Returns:
        True if valid directory, False otherwise.
    """
    if not path_str:
        return False

    path = Path(path_str)
    return path.is_dir()


def validate_optional_directory_path(path_str: str) -> bool:
    """
    Validate that a path string represents a valid directory (allows empty string).

    Args:
        path_str: Path string to validate.

    Returns:
        True if valid directory or empty string, False otherwise.
    """
    if not path_str:
        return True

    return validate_directory_path(path_str)


def interactive_setup() -> Dict[str, Any]:
    """
    Run interactive setup using questionary prompts.

    Returns:
        Dictionary containing the configuration settings.
    """
    try:
        import questionary
    except ImportError:
        print("Error: 'questionary' package is required for interactive setup.")
        print("Install it with: pip install questionary")
        sys.exit(1)

    print("FAIR Metadata System Setup")
    print("=" * 40)
    print()

    # Get monitor path
    monitor_path = questionary.text(
        "Enter the directory path to monitor:",
        default=str(Path.cwd() / "data"),
        validate=lambda text: (
            "Directory does not exist" if not validate_directory_path(text) else True
        ),
    ).ask()

    if not monitor_path:
        print("Setup cancelled.")
        sys.exit(0)

    # Get custom schema path (optional)
    custom_schema_path = questionary.text(
        "Enter custom schema directory path (optional, press Enter to skip):",
        validate=lambda text: (
            "Directory does not exist"
            if not validate_optional_directory_path(text)
            else True
        ),
    ).ask()

    # Get environment
    environment = questionary.select(
        "Select environment:",
        choices=["development", "staging", "production"],
        default="development",
    ).ask()

    # Get API port
    api_port = questionary.text(
        "Enter API port:",
        default="8000",
        validate=lambda text: (
            "Invalid port number" if not text.isdigit() or int(text) < 1 or int(text) > 65535 else True
        ),
    ).ask()

    # Show summary and confirm
    print("\nConfiguration Summary:")
    print(f"  Monitor Path: {monitor_path}")
    print(
        f"  Custom Schema Path: {custom_schema_path if custom_schema_path else 'Not set'}"
    )
    print(f"  Environment: {environment}")
    print(f"  API Port: {api_port}")
    print()

    confirmed = questionary.confirm("Save this configuration?").ask()

    if not confirmed:
        print("Setup cancelled.")
        sys.exit(0)

    # Build configuration dictionary
    config = {
        "monitor_path": monitor_path,
        "environment": environment,
        "api": {
            "port": int(api_port),
            "host": "0.0.0.0"
        }
    }

    if custom_schema_path:
        config["schemas"] = {
            "custom_path": custom_schema_path
        }

    return config


def non_interactive_setup(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Run non-interactive setup using command line arguments.

    Args:
        args: Parsed command line arguments.

    Returns:
        Dictionary containing the configuration settings.
    """
    # Validate required arguments
    if not args.monitor_path:
        print("Error: --monitor-path is required in non-interactive mode")
        sys.exit(1)

    if not validate_directory_path(args.monitor_path):
        print(f"Error: Monitor path is not a valid directory: {args.monitor_path}")
        sys.exit(1)

    if args.schema_path and not validate_directory_path(args.schema_path):
        print(f"Error: Schema path is not a valid directory: {args.schema_path}")
        sys.exit(1)

    # Build configuration dictionary
    config = {
        "monitor_path": args.monitor_path,
        "environment": args.environment or "development",
        "api": {
            "port": args.api_port or 8000,
            "host": args.api_host or "0.0.0.0"
        }
    }

    if args.schema_path:
        config["schemas"] = {
            "custom_path": args.schema_path
        }

    return config


def create_config_from_template(user_config: Dict[str, Any], config_file: str) -> bool:
    """
    Create a configuration file from template with user customizations.

    Args:
        user_config: User-provided configuration settings.
        config_file: Path to save the configuration file.

    Returns:
        True if successful, False otherwise.
    """
    template_path = Path("packaged_schemas/fair_meta_config_template.yaml")

    # If running from scripts directory, adjust path
    if not template_path.exists():
        template_path = Path(__file__).parent.parent / "packaged_schemas" / "fair_meta_config_template.yaml"

    if not template_path.exists():
        print(f"Warning: Template file not found at {template_path}")
        print("Creating minimal configuration...")
        return _create_minimal_config(user_config, config_file)

    try:
        # Load template using ConfigManager
        template_manager = ConfigManager(str(template_path))
        template_config = template_manager.load_config()

        # Merge user config with template config (user config takes precedence)
        final_config = _merge_configs(template_config, user_config)

        # Save using ConfigManager
        config_manager = ConfigManager(config_file)
        return config_manager.save_config(final_config)

    except Exception as e:
        print(f"Error creating configuration from template: {e}")
        return False


def _merge_configs(template: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge user configuration into template configuration.

    Args:
        template: Template configuration dictionary.
        user: User-provided configuration dictionary.

    Returns:
        Merged configuration dictionary.
    """
    merged = template.copy()

    # Recursively merge dictionaries
    for key, value in user.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_configs(merged[key], value)
        else:
            merged[key] = value

    return merged


def _create_minimal_config(user_config: Dict[str, Any], config_file: str) -> bool:
    """
    Create a minimal configuration when template is not available.

    Args:
        user_config: User-provided configuration settings.
        config_file: Path to save the configuration file.

    Returns:
        True if successful, False otherwise.
    """
    # Create minimal config with required fields
    minimal_config = {
        "monitor_path": user_config.get("monitor_path", "./data"),
        "environment": user_config.get("environment", "development"),
        "debug": False,
        "logging": {
            "level": "INFO"
        },
        "api": {
            "host": user_config.get("api", {}).get("host", "0.0.0.0"),
            "port": user_config.get("api", {}).get("port", 8000)
        }
    }

    # Add custom schema path if provided
    if "schemas" in user_config:
        minimal_config["schemas"] = user_config["schemas"]

    config_manager = ConfigManager(config_file)
    return config_manager.save_config(minimal_config)


def main():
    """Main function for the setup tool."""
    parser = argparse.ArgumentParser(
        description="FAIR Metadata System Setup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive setup
  python scripts/setup_config.py

  # Non-interactive setup
  python scripts/setup_config.py --monitor-path /path/to/monitor --schema-path /path/to/schemas

  # Non-interactive setup with only monitor path
  python scripts/setup_config.py --monitor-path /path/to/monitor

  # Force non-interactive mode
  python scripts/setup_config.py --non-interactive --monitor-path /path/to/monitor
        """,
    )

    parser.add_argument(
        "--monitor-path",
        type=str,
        help="Directory path to monitor (required in non-interactive mode)",
    )

    parser.add_argument(
        "--schema-path", type=str, help="Optional custom schema directory path"
    )

    parser.add_argument(
        "--environment",
        type=str,
        choices=["development", "staging", "production"],
        help="Environment name (default: development)",
    )

    parser.add_argument(
        "--api-host",
        type=str,
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--api-port",
        type=int,
        help="API server port (default: 8000)",
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Force non-interactive mode (requires --monitor-path)",
    )

    parser.add_argument(
        "--config-file",
        type=str,
        default="./.fair_meta_config.yaml",
        help="Path to save the configuration file (default: ./.fair_meta_config.yaml)",
    )

    args = parser.parse_args()

    # Determine mode
    if args.non_interactive or args.monitor_path:
        # Non-interactive mode
        print("Running in non-interactive mode...")
        user_config = non_interactive_setup(args)
    else:
        # Interactive mode
        user_config = interactive_setup()

    # Create configuration from template
    print("Creating configuration from template...")

    if create_config_from_template(user_config, args.config_file):
        print(f"\nConfiguration saved successfully to: {args.config_file}")
        print("\nNext steps:")
        print("1. Validate the configuration: python scripts/validate_config.py")
        print("2. Run the API server: uvicorn main:app --reload")
        print("3. Check the documentation for more information")
    else:
        print(f"\nFailed to save configuration to: {args.config_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
