#!/usr/bin/env python3
"""
Configuration Validation Script for FAIR Metadata System
Validates configuration files and environment setup.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.config_manager import ConfigManager
from app.core.config import initialize_config


def validate_configuration(config_path: str, environment: str = None) -> Tuple[bool, List[str]]:
    """
    Validate a configuration file.

    Args:
        config_path: Path to the configuration file
        environment: Environment name (development, staging, production)

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    try:
        # Initialize config manager
        config_manager = ConfigManager(config_path, environment)

        # Load and validate configuration
        is_valid, validation_errors = config_manager.validate_config()
        errors.extend(validation_errors)

        if not is_valid:
            return False, errors

        # Additional validations
        config = config_manager.load_config()

        # Validate environment-specific settings
        if environment:
            env_config_path = config_manager._get_environment_config_path()
            if env_config_path and not env_config_path.exists():
                errors.append(f"Environment-specific config file not found: {env_config_path}")

        # Validate file paths
        monitor_path = config_manager.get_setting('monitor_path')
        if monitor_path:
            try:
                path = Path(monitor_path)
                if not path.exists():
                    # Check if we can create it
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        print(f"Created monitor directory: {path}")
                    except Exception as e:
                        errors.append(f"Cannot create monitor directory '{monitor_path}': {e}")
            except Exception as e:
                errors.append(f"Invalid monitor_path '{monitor_path}': {e}")

        # Validate API settings
        api_config = config_manager.get_setting('api', {})
        if api_config:
            port = api_config.get('port')
            if port and (not isinstance(port, int) or port < 1 or port > 65535):
                errors.append(f"Invalid API port: {port}")

            host = api_config.get('host')
            if host and not isinstance(host, str):
                errors.append(f"Invalid API host: {host}")

        # Validate security settings
        security_config = config_manager.get_setting('security', {})
        if security_config:
            auth_config = security_config.get('authentication', {})
            if auth_config.get('enabled') and not auth_config.get('api_key'):
                errors.append("Authentication is enabled but no API key is configured")

            rate_limit_config = security_config.get('rate_limiting', {})
            if rate_limit_config.get('enabled'):
                max_requests = rate_limit_config.get('max_requests')
                if max_requests and (not isinstance(max_requests, int) or max_requests < 1):
                    errors.append(f"Invalid rate limit max_requests: {max_requests}")

        # Validate file processing settings
        file_processing_config = config_manager.get_setting('file_processing', {})
        if file_processing_config:
            checksum_algo = file_processing_config.get('checksum_algorithm')
            if checksum_algo and checksum_algo not in ['sha1', 'sha256', 'sha512', 'md5']:
                errors.append(f"Unsupported checksum algorithm: {checksum_algo}")

            chunk_size = file_processing_config.get('chunk_size')
            if chunk_size and (not isinstance(chunk_size, int) or chunk_size < 1):
                errors.append(f"Invalid chunk size: {chunk_size}")

        # Validate logging settings
        logging_config = config_manager.get_setting('logging', {})
        if logging_config:
            level = logging_config.get('level')
            if level and level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                errors.append(f"Invalid logging level: {level}")

        # Validate Redis settings
        redis_config = config_manager.get_setting('redis', {})
        if redis_config:
            port = redis_config.get('port')
            if port and (not isinstance(port, int) or port < 1 or port > 65535):
                errors.append(f"Invalid Redis port: {port}")

        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"Configuration validation failed: {e}")
        return False, errors


def check_environment_variables() -> List[str]:
    """Check for required environment variables."""
    warnings = []

    # Check for common environment variables
    env_vars_to_check = [
        'MDJOURNEY_ENV',
        'MONITOR_PATH',
        'LOG_LEVEL',
        'API_PORT',
        'REDIS_HOST',
        'REDIS_PORT',
        'DATABASE_URL',
    ]

    for var in env_vars_to_check:
        if var not in os.environ:
            warnings.append(f"Environment variable {var} is not set")

    return warnings


def print_configuration_summary(config_manager: ConfigManager):
    """Print a summary of the current configuration."""
    print("\n" + "="*60)
    print("CONFIGURATION SUMMARY")
    print("="*60)

    print(f"Environment: {config_manager.get_environment()}")
    print(f"Monitor Path: {config_manager.get_setting('monitor_path')}")
    print(f"Debug Mode: {config_manager.get_setting('debug', False)}")

    # API Configuration
    api_config = config_manager.get_setting('api', {})
    print(f"API Host: {api_config.get('host', '0.0.0.0')}")
    print(f"API Port: {api_config.get('port', 8000)}")

    # Security Configuration
    security_config = config_manager.get_setting('security', {})
    auth_enabled = security_config.get('authentication', {}).get('enabled', False)
    rate_limit_enabled = security_config.get('rate_limiting', {}).get('enabled', True)
    print(f"Authentication: {'Enabled' if auth_enabled else 'Disabled'}")
    print(f"Rate Limiting: {'Enabled' if rate_limit_enabled else 'Disabled'}")

    # File Processing Configuration
    file_config = config_manager.get_setting('file_processing', {})
    print(f"Checksum Algorithm: {file_config.get('checksum_algorithm', 'sha256')}")
    print(f"Chunk Size: {file_config.get('chunk_size', 4096)}")
    print(f"Max File Size: {file_config.get('max_file_size', '100MB')}")

    # Logging Configuration
    logging_config = config_manager.get_setting('logging', {})
    print(f"Log Level: {logging_config.get('level', 'INFO')}")

    # Version Control Configuration
    vc_config = config_manager.get_setting('version_control', {})
    git_enabled = vc_config.get('git', {}).get('enabled', True)
    dvc_enabled = vc_config.get('dvc', {}).get('enabled', True)
    print(f"Git: {'Enabled' if git_enabled else 'Disabled'}")
    print(f"DVC: {'Enabled' if dvc_enabled else 'Disabled'}")

    print("="*60)


def main():
    """Main function for configuration validation."""
    parser = argparse.ArgumentParser(description="Validate FAIR Metadata System configuration")
    parser.add_argument(
        "--config",
        "-c",
        default=".fair_meta_config.yaml",
        help="Path to configuration file (default: .fair_meta_config.yaml)"
    )
    parser.add_argument(
        "--environment",
        "-e",
        help="Environment name (development, staging, production)"
    )
    parser.add_argument(
        "--summary",
        "-s",
        action="store_true",
        help="Print configuration summary"
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check environment variables"
    )

    args = parser.parse_args()

    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)

    # Determine environment
    environment = args.environment or os.getenv('MDJOURNEY_ENV', 'development')

    print(f"Validating configuration: {config_path}")
    print(f"Environment: {environment}")

    # Validate configuration
    is_valid, errors = validate_configuration(str(config_path), environment)

    if not is_valid:
        print("\n❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ Configuration validation passed!")

    # Check environment variables if requested
    if args.check_env:
        env_warnings = check_environment_variables()
        if env_warnings:
            print("\n⚠️  Environment variable warnings:")
            for warning in env_warnings:
                print(f"  - {warning}")
        else:
            print("\n✅ All environment variables are properly set")

    # Print configuration summary if requested
    if args.summary:
        try:
            config_manager = ConfigManager(str(config_path), environment)
            print_configuration_summary(config_manager)
        except Exception as e:
            print(f"Error generating configuration summary: {e}")

    print("\nConfiguration validation completed successfully!")


if __name__ == "__main__":
    main()
