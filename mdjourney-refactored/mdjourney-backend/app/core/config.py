"""
Enhanced Configuration module for the FAIR metadata automation system.
Centralizes all global settings, paths, and configuration constants with environment support.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any

# --- Global State Variables (populated at runtime) ---
MONITOR_PATH: Optional[Path] = None
CUSTOM_SCHEMA_PATH: Optional[Path] = None
SCHEMA_PATH_OVERRIDES: Dict[str, Path] = {}
CONFIG_MANAGER: Optional[Any] = None

# --- Static Configuration Constants (fallback values) ---
PROJECT_PREFIX = "p_"
DATASET_PREFIX = "d_"
METADATA_SUBDIR = ".metadata"
STRICT_VALIDATION = True

# --- Schema File Paths ---
SCHEMA_BASE_PATH = "packaged_schemas"
PROJECT_SCHEMA_PATH = os.path.join(SCHEMA_BASE_PATH, "project_descriptive.json")
PROJECT_ADMIN_SCHEMA_PATH = os.path.join(
    SCHEMA_BASE_PATH, "project_administrative_schema.json"
)
DATASET_ADMIN_SCHEMA_PATH = os.path.join(
    SCHEMA_BASE_PATH, "dataset_administrative_schema.json"
)
DATASET_STRUCT_SCHEMA_PATH = os.path.join(
    SCHEMA_BASE_PATH, "dataset_structural_schema.json"
)
EXPERIMENT_CONTEXTUAL_SCHEMA_PATH = os.path.join(
    SCHEMA_BASE_PATH, "experiment_contextual_schema.json"
)
INSTRUMENT_TECHNICAL_SCHEMA_PATH = os.path.join(
    SCHEMA_BASE_PATH, "instrument_technical_schema.json"
)
COMPLETE_METADATA_SCHEMA_PATH = os.path.join(
    SCHEMA_BASE_PATH, "complete_metadata_schema.json"
)

# --- Metadata File Names ---
PROJECT_DESCRIPTIVE_FILENAME = "project_descriptive.json"
DATASET_ADMIN_FILENAME = "dataset_administrative.json"
DATASET_STRUCT_FILENAME = "dataset_structural.json"
EXPERIMENT_CONTEXTUAL_FILENAME = "experiment_contextual.json"


def initialize_config(config_path: str) -> bool:
    """
    Initialize the configuration from a config file.

    Args:
        config_path: Path to the configuration file (supports YAML or JSON).

    Returns:
        True if successful, False otherwise.
    """
    from .config_manager import ConfigManager

    try:
        global CONFIG_MANAGER, MONITOR_PATH, CUSTOM_SCHEMA_PATH, SCHEMA_PATH_OVERRIDES

        # Initialize the enhanced config manager
        CONFIG_MANAGER = ConfigManager(config_path)
        settings = CONFIG_MANAGER.load_config()

        # Validate configuration
        is_valid, errors = CONFIG_MANAGER.validate_config()
        if not is_valid:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        # Validate required settings
        if not CONFIG_MANAGER.get_setting('monitor_path'):
            print("Error: 'monitor_path' is required in configuration")
            return False

        # Populate global state variables
        MONITOR_PATH = Path(CONFIG_MANAGER.get_setting('monitor_path'))

        # Handle environment variable overrides with warnings
        if os.environ.get("MDJOURNEY_DATA_PATH"):
            print(
                "Note: MDJOURNEY_DATA_PATH is set but ignored; using monitor_path from configuration"
            )

        custom_path_setting = CONFIG_MANAGER.get_setting('schemas.custom_path')
        CUSTOM_SCHEMA_PATH = (
            Path(custom_path_setting)
            if custom_path_setting and custom_path_setting != 'null' and custom_path_setting.strip()
            else None
        )

        # Handle schema path overrides
        SCHEMA_PATH_OVERRIDES = {}
        schema_paths_cfg = CONFIG_MANAGER.get_setting('schemas.path_overrides', {}) or {}
        if isinstance(schema_paths_cfg, dict):
            # Map friendly keys to actual schema filenames
            key_to_filename = {
                "project_descriptive": "project_descriptive.json",
                "dataset_administrative": "dataset_administrative_schema.json",
                "dataset_structural": "dataset_structural_schema.json",
                "experiment_contextual": "experiment_contextual_schema.json",
                "instrument_technical": "instrument_technical_schema.json",
                "complete_metadata": "complete_metadata_schema.json",
            }
            for key, path_str in schema_paths_cfg.items():
                try:
                    override_path = Path(path_str)
                    if not override_path.is_absolute():
                        # Resolve relative to config file location
                        override_path = (
                            Path(config_path).parent / override_path
                        ).resolve()
                    # Determine the schema filename this override applies to
                    filename = key_to_filename.get(key, None)
                    if filename is None:
                        # If key looks like a filename, use it directly
                        filename = Path(key).name
                    SCHEMA_PATH_OVERRIDES[filename] = override_path
                except Exception:
                    continue

        # Validate paths
        if not MONITOR_PATH.exists():
            print(f"Warning: Monitor path does not exist: {MONITOR_PATH}")
            print("Creating monitor directory...")
            MONITOR_PATH.mkdir(parents=True, exist_ok=True)

        if CUSTOM_SCHEMA_PATH and not CUSTOM_SCHEMA_PATH.exists():
            print(f"Warning: Custom schema path does not exist: {CUSTOM_SCHEMA_PATH}")

        print(f"Configuration loaded successfully")
        return True

    except Exception as e:
        print(f"Error initializing configuration: {e}")
        return False


def get_config_manager():
    """Get the global configuration manager instance."""
    if CONFIG_MANAGER is None:
        raise RuntimeError(
            "Configuration not initialized. Call initialize_config() first."
        )
    return CONFIG_MANAGER


def get_config_value(key: str, default_value: Any = None) -> Any:
    """
    Get a configuration value using dot notation.

    Args:
        key: Configuration key (e.g., 'api.port', 'logging.level')
        default_value: Default value if key doesn't exist

    Returns:
        Configuration value or default_value
    """
    if CONFIG_MANAGER is None:
        return default_value
    return CONFIG_MANAGER.get_setting(key, default_value)


def get_api_config() -> Dict[str, Any]:
    """Get API configuration."""
    return get_config_value('api', {})


def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    return get_config_value('security', {})


def get_file_processing_config() -> Dict[str, Any]:
    """Get file processing configuration."""
    return get_config_value('file_processing', {})


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration."""
    return get_config_value('logging', {})


def get_version_control_config() -> Dict[str, Any]:
    """Get version control configuration."""
    return get_config_value('version_control', {})


def get_monitor_config() -> Dict[str, Any]:
    """Get monitor configuration."""
    return get_config_value('monitor', {})


def get_database_config() -> Dict[str, Any]:
    """Get database configuration."""
    return get_config_value('database', {})


def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration."""
    return get_config_value('redis', {})


def get_frontend_config() -> Dict[str, Any]:
    """Get frontend configuration."""
    return get_config_value('frontend', {})


def get_environment() -> str:
    """Get the current environment."""
    if CONFIG_MANAGER is None:
        return 'development'
    return CONFIG_MANAGER.get_environment()


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return get_config_value('debug', False)


def get_log_level() -> str:
    """Get the logging level."""
    return get_config_value('logging.level', 'INFO')


def get_api_port() -> int:
    """Get the API port."""
    return get_config_value('api.port', 8000)


def get_api_host() -> str:
    """Get the API host."""
    return get_config_value('api.host', '0.0.0.0')


def get_cors_origins() -> list:
    """Get CORS allowed origins."""
    return get_config_value('api.cors.origins', ['http://localhost:5173'])


def get_rate_limit_config() -> Dict[str, Any]:
    """Get rate limiting configuration."""
    return get_config_value('security.rate_limiting', {})


def get_checksum_algorithm() -> str:
    """Get the checksum algorithm."""
    return get_config_value('file_processing.checksum_algorithm', 'sha256')


def get_chunk_size() -> int:
    """Get the file chunk size."""
    return get_config_value('file_processing.chunk_size', 4096)


def get_max_file_size() -> str:
    """Get the maximum file size."""
    return get_config_value('file_processing.max_file_size', '100MB')


def get_supported_formats() -> list:
    """Get supported file formats."""
    return get_config_value('file_processing.supported_formats', ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'pdf', 'txt', 'csv', 'json', 'xml'])


def is_strict_validation() -> bool:
    """Check if strict validation is enabled."""
    return get_config_value('schemas.strict_validation', True)


def allow_missing_schemas() -> bool:
    """Check if missing schemas are allowed."""
    return get_config_value('schemas.allow_missing_schemas', False)


def is_git_enabled() -> bool:
    """Check if Git is enabled."""
    return get_config_value('version_control.git.enabled', True)


def is_dvc_enabled() -> bool:
    """Check if DVC is enabled."""
    return get_config_value('version_control.dvc.enabled', True)


def get_git_commit_prefix() -> str:
    """Get Git commit message prefix."""
    return get_config_value('version_control.git.commit_message_prefix', 'FAIR Metadata:')


def get_git_author_name() -> str:
    """Get Git author name."""
    return get_config_value('version_control.git.author_name', 'FAIR Metadata System')


def get_git_author_email() -> str:
    """Get Git author email."""
    return get_config_value('version_control.git.author_email', 'metadata@example.com')


def get_dvc_remote() -> str:
    """Get DVC remote name."""
    return get_config_value('version_control.dvc.remote', 'local')


def get_dvc_cache_dir() -> str:
    """Get DVC cache directory."""
    return get_config_value('version_control.dvc.cache_dir', './.dvc/cache')


def get_monitor_recursive() -> bool:
    """Check if monitor should be recursive."""
    return get_config_value('monitor.recursive', True)


def get_monitor_ignore_patterns() -> list:
    """Get monitor ignore patterns."""
    return get_config_value('monitor.ignore_patterns', ['.git', '.dvc', '__pycache__', '.DS_Store'])


def get_monitor_scan_interval() -> int:
    """Get monitor scan interval in seconds."""
    return get_config_value('monitor.scan_interval_seconds', 30)


def get_database_url() -> str:
    """Get database URL."""
    return get_config_value('database.url', 'sqlite:///./data/metadata.db')


def get_redis_host() -> str:
    """Get Redis host."""
    return get_config_value('redis.host', 'localhost')


def get_redis_port() -> int:
    """Get Redis port."""
    return get_config_value('redis.port', 6379)


def get_redis_db() -> int:
    """Get Redis database number."""
    return get_config_value('redis.db', 0)


def get_redis_password() -> Optional[str]:
    """Get Redis password."""
    return get_config_value('redis.password')


def get_frontend_api_base_url() -> str:
    """Get frontend API base URL."""
    return get_config_value('frontend.api_base_url', 'http://localhost:8000')


def get_frontend_timeout() -> int:
    """Get frontend API timeout."""
    return get_config_value('frontend.timeout', 10000)


def get_monitor_path() -> Path:
    """Get the monitor path as a Path object."""
    if MONITOR_PATH is None:
        raise RuntimeError(
            "Configuration not initialized. Call initialize_config() first."
        )
    return MONITOR_PATH


def get_schema_path(schema_name: str) -> Path:
    """Get the full path to a schema file."""
    return Path(SCHEMA_BASE_PATH) / schema_name


def get_metadata_dir(base_path: Path) -> Path:
    """Get the metadata directory for a given base path."""
    return base_path / METADATA_SUBDIR


def ensure_monitor_path_exists() -> Path:
    """Ensure the monitor directory exists."""
    monitor_path = get_monitor_path()
    monitor_path.mkdir(exist_ok=True)
    return monitor_path


def reload_config_from_environment() -> bool:
    """Reload configuration from environment variables (for testing)."""
    global MONITOR_PATH, CUSTOM_SCHEMA_PATH

    changed = False

    monitor_path_override = os.environ.get("MDJOURNEY_DATA_PATH")
    if monitor_path_override:
        MONITOR_PATH = Path(monitor_path_override)
        print(f"Reloaded monitor path from environment: {MONITOR_PATH}")
        MONITOR_PATH.mkdir(parents=True, exist_ok=True)
        changed = True

    custom_schema_override = os.environ.get("MDJOURNEY_SCHEMA_PATH")
    if custom_schema_override:
        CUSTOM_SCHEMA_PATH = Path(custom_schema_override)
        print(f"Reloaded custom schema path from environment: {CUSTOM_SCHEMA_PATH}")
        changed = True

    return changed


def set_monitor_path(path_str: str) -> bool:
    """Programmatically set the monitor path (used by tests or admin tools)."""
    global MONITOR_PATH
    try:
        path = Path(path_str)
        path.mkdir(parents=True, exist_ok=True)
        MONITOR_PATH = path
        print(f"Monitor path set programmatically: {MONITOR_PATH}")
        return True
    except Exception as e:
        print(f"Failed to set monitor path: {e}")
        return False


def set_custom_schema_path(path_str: str) -> bool:
    """Programmatically set the custom schema directory path."""
    global CUSTOM_SCHEMA_PATH
    try:
        path = Path(path_str)
        if not path.exists():
            print(f"Warning: Custom schema path does not exist: {path}")
        CUSTOM_SCHEMA_PATH = path
        print(f"Custom schema path set programmatically: {CUSTOM_SCHEMA_PATH}")
        return True
    except Exception as e:
        print(f"Failed to set custom schema path: {e}")
        return False


def find_config_file() -> Optional[Path]:
    """
    Find the configuration file by searching current directory and parent directories.

    Returns:
        Path to the configuration file if found, None otherwise.
    """
    config_names = [".fair_meta_config.yaml", ".fair_meta_config.yml", "fair_meta_config.yaml", "fair_meta_config.yml"]
    current_dir = Path.cwd()

    # Search current directory and parent directories
    for directory in [current_dir] + list(current_dir.parents):
        for config_name in config_names:
            config_path = directory / config_name
            if config_path.exists():
                return config_path

        # Fallback: look for config inside a nested 'mdjourney' folder commonly used in this repo
        for config_name in config_names:
            nested_config = directory / "mdjourney" / config_name
            if nested_config.exists():
                return nested_config

    # Final fallback: resolve relative to this module location (project mdjourney root)
    try:
        this_file = Path(__file__).resolve()
        mdjourney_root = this_file.parent.parent.parent
        for config_name in config_names:
            cfg = mdjourney_root / config_name
            if cfg.exists():
                return cfg
    except Exception:
        pass

    return None
