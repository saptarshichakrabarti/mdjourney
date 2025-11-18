# Configuration Management System

This document describes the enhanced configuration management system for the FAIR Metadata Automation project.

## Overview

The configuration management system provides:
- **Environment-specific configurations** (development, staging, production)
- **Environment variable substitution** with fallback values
- **Configuration validation** and error handling
- **Dynamic configuration loading** with caching
- **Migration tools** for upgrading from old configuration formats

## Configuration Structure
## Quick Start

If you're setting up the system for the first time (especially for the decoupled architecture), run the initial configuration to create `.fair_meta_config.yaml` and point the monitor to the directory to watch:

```bash
make setup
```

This is a one-time step on the remote/back-end machine.


### Base Configuration File

The main configuration file (`.fair_meta_config.yaml`) contains the base configuration with sensible defaults:

```yaml
# Required settings
monitor_path: "./data"

# Application settings
environment: "development"
debug: false

# API server settings
api:
  host: "0.0.0.0"
  port: 8000
  cors:
    origins: ["http://localhost:5173", "http://localhost:3000"]

# Security settings
security:
  authentication:
    enabled: false
    api_key: "your-secure-api-key-here"
  rate_limiting:
    enabled: true
    max_requests: 1000
    window_seconds: 3600

# File processing settings
file_processing:
  checksum_algorithm: "sha256"
  chunk_size: 4096
  max_file_size: "100MB"

# And many more...
```

### Environment-Specific Configurations

Environment-specific configurations override the base configuration:

- `configs/development.yaml` - Development environment settings
- `configs/staging.yaml` - Staging environment settings
- `configs/production.yaml` - Production environment settings

Example development configuration:
```yaml
environment: "development"
debug: true
logging:
  level: "DEBUG"
api:
  reload: true
  cors:
    origins: ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
security:
  authentication:
    enabled: false
  rate_limiting:
    enabled: false
```

## Environment Variable Substitution

The configuration system supports environment variable substitution using the `${VAR_NAME}` or `${VAR_NAME:-default}` syntax:

```yaml
security:
  authentication:
    api_key: "${MDJOURNEY_API_KEY:-your-secure-api-key-here}"
database:
  url: "${DATABASE_URL}"
redis:
  host: "${REDIS_HOST:-localhost}"
  port: "${REDIS_PORT:-6379}"
```

## Usage

### Basic Usage

```python
from app.core.config import initialize_config, get_config_value

# Initialize configuration
success = initialize_config(".fair_meta_config.yaml")

# Get configuration values
api_port = get_config_value('api.port', 8000)
debug_mode = get_config_value('debug', False)
cors_origins = get_config_value('api.cors.origins', [])
```

### Using Configuration Manager Directly

```python
from app.core.config_manager import ConfigManager

# Initialize config manager
config_manager = ConfigManager(".fair_meta_config.yaml", environment="production")

# Load configuration
config = config_manager.load_config()

# Get specific settings
monitor_path = config_manager.get_setting('monitor_path')
api_config = config_manager.get_setting('api', {})

# Validate configuration
is_valid, errors = config_manager.validate_config()
```

### Helper Functions

The system provides many helper functions for common configuration access:

```python
from app.core.config import (
    get_api_port, get_api_host, get_cors_origins,
    get_checksum_algorithm, get_chunk_size,
    is_debug_mode, get_log_level,
    is_git_enabled, is_dvc_enabled,
    get_redis_host, get_redis_port,
    get_frontend_api_base_url
)

# Use helper functions
port = get_api_port()  # Returns configured API port
debug = is_debug_mode()  # Returns True/False
redis_host = get_redis_host()  # Returns Redis host
```

## Environment Variables

The system respects the following environment variables:

### Core Environment Variables
- `MDJOURNEY_ENV` - Environment name (development, staging, production)
- `MONITOR_PATH` - Path to monitor directory
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### API Configuration
- `API_HOST` - API server host
- `API_PORT` - API server port
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins

### Security Configuration
- `MDJOURNEY_API_KEY` - API key for authentication
- `ENABLE_AUTHENTICATION` - Enable/disable authentication
- `RATE_LIMIT_REQUESTS` - Maximum requests per window
- `RATE_LIMIT_WINDOW` - Rate limit window in seconds

### Database Configuration
- `DATABASE_URL` - Database connection URL
- `REDIS_HOST` - Redis server host
- `REDIS_PORT` - Redis server port
- `REDIS_PASSWORD` - Redis password

### Frontend Configuration
- `VITE_API_BASE_URL` - Frontend API base URL
- `VITE_API_TIMEOUT` - Frontend API timeout

## Docker Configuration

### Production Docker Compose

```yaml
services:
  api:
    environment:
      - MDJOURNEY_ENV=production
      - MDJOURNEY_API_KEY=${MDJOURNEY_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_HOST=${REDIS_HOST:-redis}
      - REDIS_PORT=${REDIS_PORT:-6379}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    ports:
      - "${API_PORT:-8000}:8000"
```

### Development Docker Compose

```yaml
services:
  api:
    environment:
      - MDJOURNEY_ENV=development
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
```

## Configuration Validation

### Using the Validation Script

```bash
# Validate configuration
python scripts/validate_config.py --config .fair_meta_config.yaml

# Validate with environment
python scripts/validate_config.py --config .fair_meta_config.yaml --environment production

# Print configuration summary
python scripts/validate_config.py --config .fair_meta_config.yaml --summary

# Check environment variables
python scripts/validate_config.py --config .fair_meta_config.yaml --check-env
```

### Programmatic Validation

```python
from app.core.config_manager import ConfigManager

config_manager = ConfigManager(".fair_meta_config.yaml")
is_valid, errors = config_manager.validate_config()

if not is_valid:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
```

## Migration from Old Configuration

### Using the Migration Script

```bash
# Migrate old configuration
python scripts/migrate_config.py --old-config old_config.yaml

# Migrate with custom output path
python scripts/migrate_config.py --old-config old_config.yaml --new-config new_config.yaml

# Create environment-specific configs
python scripts/migrate_config.py --old-config old_config.yaml --create-env-configs
```

### Manual Migration

1. **Update configuration structure**: Move from flat key-value pairs to nested structure
2. **Add environment-specific files**: Create `configs/development.yaml`, `configs/staging.yaml`, `configs/production.yaml`
3. **Replace hardcoded values**: Use environment variable substitution where appropriate
4. **Update application code**: Replace direct config access with helper functions

## Best Practices

### Configuration Organization

1. **Use environment-specific configs** for different deployment environments
2. **Keep sensitive data in environment variables** (API keys, passwords, etc.)
3. **Use descriptive default values** for optional settings
4. **Validate configurations** before deployment

### Security Considerations

1. **Never commit sensitive data** to configuration files
2. **Use environment variable substitution** for secrets
3. **Enable authentication in production** environments
4. **Configure appropriate CORS origins** for production

### Development Workflow

1. **Start with base configuration** for common settings
2. **Override in environment configs** for environment-specific needs
3. **Use environment variables** for deployment-specific values
4. **Validate configurations** before committing changes

## Troubleshooting

### Common Issues

1. **Configuration not loading**: Check file paths and YAML syntax
2. **Environment variables not substituted**: Ensure correct `${VAR_NAME}` syntax
3. **Validation errors**: Check required fields and data types
4. **Environment-specific configs not found**: Verify file locations and naming

### Debug Configuration Loading

```python
from app.core.config_manager import ConfigManager

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Load configuration with debug info
config_manager = ConfigManager(".fair_meta_config.yaml", environment="development")
config = config_manager.load_config()
print(f"Loaded config: {config}")
```

### Configuration Validation

```python
# Validate configuration
is_valid, errors = config_manager.validate_config()
if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

## API Reference

### ConfigManager Class

- `__init__(config_path, environment=None)` - Initialize config manager
- `load_config()` - Load configuration with environment overrides
- `get_setting(key, default_value=None)` - Get configuration value using dot notation
- `update_setting(key, value)` - Update configuration value
- `validate_config()` - Validate configuration
- `reload_config()` - Clear cache and reload configuration

### Configuration Helper Functions

- `get_config_value(key, default_value=None)` - Get configuration value
- `get_api_config()` - Get API configuration
- `get_security_config()` - Get security configuration
- `get_file_processing_config()` - Get file processing configuration
- `is_debug_mode()` - Check if debug mode is enabled
- `get_log_level()` - Get logging level
- `get_api_port()` - Get API port
- `get_cors_origins()` - Get CORS origins
- And many more...

## Examples

### Complete Configuration Example

See `packaged_schemas/fair_meta_config_template.yaml` for a complete configuration template.

### Environment-Specific Examples

- `configs/development.yaml` - Development environment
- `configs/staging.yaml` - Staging environment
- `configs/production.yaml` - Production environment

### Docker Compose Examples

- `docker-compose.yml` - Production deployment
- `docker-compose.dev.yml` - Development deployment
