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
project_root = Path(__file__).parent
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
        default=str(Path.cwd()),
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

    # Show summary and confirm
    print("\nConfiguration Summary:")
    print(f"  Monitor Path: {monitor_path}")
    print(
        f"  Custom Schema Path: {custom_schema_path if custom_schema_path else 'Not set'}"
    )
    print()

    confirmed = questionary.confirm("Save this configuration?").ask()

    if not confirmed:
        print("Setup cancelled.")
        sys.exit(0)

    # Build configuration dictionary
    config = {"monitor_path": monitor_path}

    if custom_schema_path:
        config["custom_schema_path"] = custom_schema_path

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
    config = {"monitor_path": args.monitor_path}

    if args.schema_path:
        config["custom_schema_path"] = args.schema_path

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

    if not template_path.exists():
        print(f"Warning: Template file not found at {template_path}")
        print("Creating minimal configuration...")
        return _create_minimal_config(user_config, config_file)

    try:
        # Read the template as a string to preserve structure
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        # Apply user customizations
        final_content = _apply_user_customizations(template_content, user_config)

        # Save the final configuration
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as file:
            file.write(final_content)

        return True

    except Exception as e:
        print(f"Error creating configuration from template: {e}")
        return False


def _create_minimal_config(user_config: Dict[str, Any], config_file: str) -> bool:
    """
    Create a minimal configuration when template is not available.

    Args:
        user_config: User-provided configuration settings.
        config_file: Path to save the configuration file.

    Returns:
        True if successful, False otherwise.
    """
    config_manager = ConfigManager(config_file)
    return config_manager.save_config(user_config)


def _apply_user_customizations(
    template_content: str, user_config: Dict[str, Any]
) -> str:
    """
    Apply user customizations to the template content.

    Args:
        template_content: Raw template content as string.
        user_config: User-provided configuration settings.

    Returns:
        Modified template content with user customizations applied.
    """
    lines = template_content.split("\n")
    modified_lines = []

    for line in lines:
        # Check if this line contains a user-configurable setting
        if line.strip().startswith("monitor_path:"):
            if "monitor_path" in user_config:
                modified_lines.append(f"monitor_path: {user_config['monitor_path']}")
            else:
                modified_lines.append(line)
        elif line.strip().startswith("# custom_schema_path:"):
            if (
                "custom_schema_path" in user_config
                and user_config["custom_schema_path"]
            ):
                # Uncomment and set the custom schema path
                modified_lines.append(
                    f"custom_schema_path: {user_config['custom_schema_path']}"
                )
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

    return "\n".join(modified_lines)


def main():
    """Main function for the setup tool."""
    parser = argparse.ArgumentParser(
        description="FAIR Metadata System Setup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive setup
  python setup_config.py

  # Non-interactive setup
  python setup_config.py --monitor-path /path/to/monitor --schema-path /path/to/schemas

  # Non-interactive setup with only monitor path
  python setup_config.py --monitor-path /path/to/monitor

  # Force non-interactive mode
  python setup_config.py --non-interactive --monitor-path /path/to/monitor
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
        print("1. Run the monitor: python scripts/run_monitor.py")
        print("2. Run the API: python api/run_api.py")
        print("3. Check the documentation for more information")
    else:
        print(f"\nFailed to save configuration to: {args.config_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
