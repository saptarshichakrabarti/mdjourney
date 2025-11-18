# Virtual Environment Setup Guide

This guide explains the **automatic virtual environment management** for the MDJourney backend system.

## Overview

The system **automatically creates and manages** a Python virtual environment (`.venv`) for all backend operations. You don't need to manually create or activate virtual environments - everything is handled automatically!

## Quick Start

### 1. One-Command Setup
```bash
make install
```
This automatically creates the virtual environment and installs all dependencies.

### 2. Start Services
```bash
make start
```
This automatically uses the virtual environment to run the backend services.

## Virtual Environment Commands

### Core Commands
```bash
# Create virtual environment
make venv-create

# Install dependencies in virtual environment
make venv-install

# Remove virtual environment
make venv-clean
```

### Service Commands (Auto-use Virtual Environment)
```bash
# Start all services
make start

# Start API only
make start-api

# Start monitor only
make start-monitor

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Type checking
make type-check
```

## How It Works

1. **Automatic Creation**: All backend commands automatically create the virtual environment if it doesn't exist
2. **Idempotent Operations**: Commands can be run multiple times safely
3. **No Manual Activation**: You never need to manually activate/deactivate the virtual environment
4. **Clean Isolation**: Each project gets its own isolated Python environment

## Manual Virtual Environment Usage (Optional)

If you prefer to work with the virtual environment manually:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run commands normally
python manage.py start
python manage.py test

# Deactivate when done
deactivate
```

## Benefits

- **Isolated Dependencies**: No conflicts with system Python packages
- **Reproducible Environment**: Same Python version and packages across systems
- **Easy Cleanup**: Remove `.venv/` directory to reset environment
- **Automatic Management**: No need to remember to activate/deactivate
- **Zero Configuration**: Just run commands - everything is handled automatically

## Troubleshooting

### Permission Issues
If you encounter permission issues, ensure you have write access to the project directory.

### Python Version Issues
The virtual environment uses `python3` by default. If you need a specific Python version, modify the `PYTHON` variable in the Makefile.

## Development Workflow

### New Developer Setup
```bash
# Clone repository
git clone <repository-url>
cd mdjourney-dev

# One-command setup (creates venv automatically)
make install

# Start development (uses venv automatically)
make start
```

### Daily Development
```bash
# Start services (creates venv automatically if needed)
make start

# Run tests (creates venv automatically if needed)
make test

# Format code (creates venv automatically if needed)
make format
```

### Clean Reset
```bash
# Remove virtual environment and recreate
make clean-all
make install
```

## Integration with Other Tools

### IDE Integration
Most IDEs can detect and use the `.venv` directory automatically:
- **VS Code**: Select Python interpreter from `.venv/bin/python`
- **PyCharm**: Configure project interpreter to use `.venv/bin/python`
- **Vim/Neovim**: Use plugins that detect virtual environments

### CI/CD Integration
For automated environments, you can still use the virtual environment:
```bash
# In CI scripts
make venv-create
make venv-install
make test
```

This ensures consistent behavior between local development and automated testing.
