"""
Configuration Manager for the FAIR metadata automation system.
Handles reading from and writing to configuration files with variable substitution.
Supports both YAML and JSON configuration formats for gateway compatibility.
"""

import os
import re
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigManager:
    """Configuration manager with variable substitution support."""

    def __init__(self, config_path: str):
        """
        Initialize the ConfigManager with a configuration file path.

        Args:
            config_path: Path to the configuration file (supports .yaml, .yml, .json)
        """
        self.config_path = Path(config_path)
        self._config_cache: Optional[Dict[str, Any]] = None
        self._is_json = self.config_path.suffix.lower() in ['.json']

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the file (YAML or JSON).

        Returns:
            Dictionary containing the loaded configuration.
            Returns empty dictionary if file doesn't exist.
        """
        if self._config_cache is not None:
            return self._config_cache

        try:
            if not self.config_path.exists():
                print(f"Warning: Configuration file not found: {self.config_path}")
                return {}

            # Load configuration based on file type
            if self._is_json:
                config = self._load_json_file(self.config_path)
            else:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install pyyaml")
                config = self._load_yaml_file(self.config_path)

            # Substitute environment variables
            final_config = self._substitute_env_vars(config)

            # Map gateway-style config keys to internal format
            final_config = self._normalize_config_keys(final_config)

            # Cache the result
            self._config_cache = final_config
            return final_config

        except Exception as e:
            print(f"Warning: Could not load configuration: {e}")
            return {}

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a YAML file and return its contents as a dictionary."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                config: Dict[str, Any] = yaml.safe_load(file)
                return config if config is not None else {}
        except (yaml.YAMLError, IOError) as e:
            print(f"Warning: Could not load YAML file {file_path}: {e}")
            return {}

    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a JSON file and return its contents as a dictionary."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                config: Dict[str, Any] = json.load(file)
                return config if config is not None else {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load JSON file {file_path}: {e}")
            return {}

    def _substitute_env_vars(self, config: Union[Dict[str, Any], list, str, int, float, bool]) -> Any:
        """Recursively substitute environment variables in configuration values."""
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_string_env_vars(config)
        else:
            return config

    def _substitute_string_env_vars(self, value: str) -> str:
        """Substitute environment variables in a string value."""
        # Pattern to match ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.getenv(var_name, default_value)

        return re.sub(pattern, replace_var, value)

    def _normalize_config_keys(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize configuration keys from gateway format to internal format.

        Gateway uses camelCase (watchDirectory, templateDirectory, watchPatterns)
        Internal format uses snake_case (monitor_path, template_directory, watch_patterns)
        """
        normalized = {}

        # Map gateway keys to internal keys
        key_mapping = {
            'watchDirectory': 'monitor_path',
            'templateDirectory': 'template_directory',
            'watchPatterns': 'watch_patterns',
            'metadataSchema': 'metadata_schema'
        }

        for key, value in config.items():
            # Use mapped key if available, otherwise keep original
            normalized_key = key_mapping.get(key, key)

            # Recursively normalize nested dictionaries
            if isinstance(value, dict):
                normalized[normalized_key] = self._normalize_config_keys(value)
            else:
                normalized[normalized_key] = value

        return normalized

    def load_template_config(self) -> str:
        """
        Load the raw template configuration as a string to preserve comments.

        Returns:
            Raw template configuration string.
        """
        try:
            if not self.config_path.exists():
                return ""

            with open(self.config_path, "r", encoding="utf-8") as file:
                return file.read()

        except (IOError, UnicodeDecodeError) as e:
            print(
                f"Warning: Could not load template configuration from {self.config_path}: {e}"
            )
            return ""

    def save_config(self, settings_dict: Dict[str, Any]) -> bool:
        """
        Save configuration to the file.

        Args:
            settings_dict: Dictionary containing the configuration settings to save.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure the directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            if self._is_json:
                with open(self.config_path, "w", encoding="utf-8") as file:
                    json.dump(settings_dict, file, indent=2, default=str)
            else:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install pyyaml")
                with open(self.config_path, "w", encoding="utf-8") as file:
                    yaml.dump(settings_dict, file, default_flow_style=False, indent=2)

            # Clear cache to force reload
            self._config_cache = None
            return True

        except (yaml.YAMLError, json.JSONDecodeError, IOError) as e:
            print(f"Error: Could not save configuration to {self.config_path}: {e}")
            return False

    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """
        Safely retrieve a setting from the loaded config using dot notation.

        Args:
            key: The configuration key to retrieve (supports dot notation like 'api.port').
            default_value: Default value if key doesn't exist.

        Returns:
            The configuration value or default_value if not found.
        """
        config = self.load_config()
        return self._get_nested_value(config, key, default_value)

    def _get_nested_value(self, config: Dict[str, Any], key: str, default_value: Any = None) -> Any:
        """Get a nested value from config using dot notation."""
        keys = key.split('.')
        value = config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default_value

    def update_setting(self, key: str, value: Any) -> bool:
        """
        Update a single setting in the configuration file using dot notation.

        Args:
            key: The configuration key to update (supports dot notation).
            value: The new value for the key.

        Returns:
            True if successful, False otherwise.
        """
        config = self.load_config()
        self._set_nested_value(config, key, value)
        return self.save_config(config)

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set a nested value in config using dot notation."""
        keys = key.split('.')
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def reload_config(self) -> Dict[str, Any]:
        """Clear cache and reload configuration."""
        self._config_cache = None
        return self.load_config()

    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Validate the loaded configuration.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        config = self.load_config()
        errors = []

        # Required fields validation
        required_fields = ['monitor_path']
        for field in required_fields:
            if not self._get_nested_value(config, field):
                errors.append(f"Required field '{field}' is missing or empty")

        # Validate monitor_path exists or can be created
        monitor_path = self._get_nested_value(config, 'monitor_path')
        if monitor_path:
            try:
                path = Path(monitor_path)
                if not path.exists():
                    # Try to create it
                    path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot access or create monitor_path '{monitor_path}': {e}")

        # Validate API settings if present
        api_port = self._get_nested_value(config, 'api.port')
        if api_port and (not isinstance(api_port, int) or api_port < 1 or api_port > 65535):
            errors.append("API port must be a valid port number (1-65535)")

        # Validate logging level if present
        log_level = self._get_nested_value(config, 'logging.level')
        if log_level and log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append("Logging level must be one of: DEBUG, INFO, WARNING, ERROR")

        return len(errors) == 0, errors

    def get_environment(self) -> str:
        """
        Get the current environment from configuration.

        Returns:
            Environment name (development, staging, production)
        """
        return self.get_setting('environment', 'development')
