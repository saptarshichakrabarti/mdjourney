# Contributing to MDJourney

This document provides comprehensive guidelines for contributing to the MDJourney FAIR Metadata Automation System. It outlines the development environment setup, coding standards, testing requirements, documentation standards, and the contribution workflow.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Contribution Workflow](#contribution-workflow)
- [Code Review Process](#code-review-process)
- [Release Process](#release-process)

## Code of Conduct

Contributors are expected to maintain professional and respectful communication. All contributions should adhere to academic and scientific standards of rigor and clarity.

## Getting Started

### Prerequisites

Before contributing, ensure you have the following installed:

- **Python 3.8 or higher**: Core development language
- **Node.js 18 or higher**: Frontend development
- **Git**: Version control system
- **Docker and Docker Compose**: Container development and testing (recommended)
- **DVC**: Data version control (optional, for testing version control features)

### Repository Setup

1. **Fork the Repository**

   Fork the repository on GitHub, then clone your fork:

   ```bash
   git clone https://github.com/your-username/mdjourney.git
   cd mdjourney-refactored
   ```

2. **Set Up Upstream Remote**

   Add the upstream repository as a remote:

   ```bash
   git remote add upstream https://github.com/saptarshichakrabarti/mdjourney.git
   git remote -v
   ```

3. **Create Development Branch**

   Create a branch for your work:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### Backend Development Setup

1. **Create Virtual Environment**

   ```bash
   cd mdjourney-backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**

   ```bash
   # Upgrade pip
   pip install --upgrade pip

   # Install development dependencies
   pip install -e ".[dev,test,api]"
   ```

3. **Install Pre-commit Hooks**

   ```bash
   pre-commit install
   ```

4. **Configure Development Environment**

   ```bash
   # Create development configuration
   python scripts/setup_config.py
   ```

### Frontend Development Setup

1. **Install Dependencies**

   ```bash
   cd mdjourney-webapp
   npm install
   ```

2. **Configure Environment Variables**

   Create `.env.local` file:

   ```bash
   VITE_API_BASE_URL=http://localhost:8080
   VITE_API_TIMEOUT=30000
   ```

### Gateway Development Setup

1. **Install Dependencies**

   ```bash
   cd mdjourney-gateway
   pip install -r requirements.txt
   ```

## Coding Standards

### Python Code Style

The project adheres to PEP 8 style guidelines with the following tools:

- **Black**: Code formatting (line length: 88 characters)
- **isort**: Import sorting (profile: black)
- **flake8**: Style and complexity checking
- **mypy**: Static type checking
- **pylint**: Code analysis

#### Formatting

Run code formatting before committing:

```bash
make format
```

This runs Black and isort to ensure consistent formatting.

#### Type Hints

All functions should include type hints:

```python
from typing import Dict, List, Optional

def process_metadata(
    dataset_id: str,
    metadata_type: str,
    content: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Process metadata for a dataset."""
    pass
```

#### Docstrings

Follow Google-style docstrings:

```python
def generate_project_metadata(project_path: Path) -> Dict[str, Any]:
    """
    Generate project-level metadata from directory structure.

    Args:
        project_path: Path to the project directory.

    Returns:
        Dictionary containing project metadata.

    Raises:
        ValueError: If project_path is not a valid project directory.
    """
    pass
```

### TypeScript/JavaScript Code Style

Frontend code follows these conventions:

- **ESLint**: Code linting with React-specific rules
- **Prettier**: Code formatting (configured via ESLint)
- **TypeScript**: Strict type checking enabled

#### Component Structure

```typescript
import React from 'react';
import { ComponentProps } from '../types';

interface MetadataEditorProps {
  datasetId: string;
  metadataType: string;
  onSave: (data: ComponentProps) => void;
}

export const MetadataEditor: React.FC<MetadataEditorProps> = ({
  datasetId,
  metadataType,
  onSave,
}) => {
  // Component implementation
};
```

### Code Organization

- **Backend**: Organized by functional modules (`app/core/`, `app/services/`, `app/monitors/`)
- **Frontend**: Component-based architecture with separation of concerns
- **Gateway**: Minimal service layer for session and request routing

### Naming Conventions

- **Python**: snake_case for variables and functions, PascalCase for classes
- **TypeScript**: camelCase for variables and functions, PascalCase for components and types
- **Files**: Descriptive names matching their primary export or functionality

## Testing Requirements

### Test Structure

Tests are organized in `mdjourney-backend/tests/`:

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for component interactions
- `regression/`: Regression tests for bug fixes
- `stress_tests/`: Performance and load testing

### Writing Tests

#### Unit Tests

```python
import pytest
from app.services.metadata_generator import MetadataGenerator

def test_generate_project_metadata():
    """Test project metadata generation."""
    generator = MetadataGenerator()
    result = generator.generate_project_metadata("p_TestProject")
    assert result["project_identifier"] is not None
    assert result["project_title"] == ""
```

#### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from main import app

def test_list_projects():
    """Test project listing endpoint."""
    client = TestClient(app)
    response = client.get("/v1/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test suite
make test-unit
make test-integration

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Coverage Requirements

- Minimum 80% code coverage for new code
- All critical paths must have test coverage
- Integration tests required for API endpoints

## Documentation Standards

### Code Documentation

- All public functions and classes must have docstrings
- Complex algorithms should include inline comments explaining logic
- Type hints are required for all function signatures

### Documentation Files

Documentation follows these guidelines:

- **Formal Academic Tone**: Use formal, academic language appropriate for scientific software
- **Comprehensive Coverage**: Document all public APIs, configuration options, and workflows
- **Examples**: Include practical examples for common use cases
- **Structure**: Use clear hierarchical organization with table of contents for longer documents

### Updating Documentation

When adding features:

1. Update relevant documentation files
2. Add examples to appropriate how-to guides
3. Update API endpoint documentation if applicable
4. Update codebase glossary for new concepts or components

## Contribution Workflow

### 1. Planning

Before starting work:

- Check existing issues and pull requests
- Discuss major changes in an issue first
- Ensure the change aligns with project goals

### 2. Development

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/descriptive-feature-name
   ```

2. **Make Changes**

   - Write code following coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Commit Changes**

   Use descriptive commit messages:

   ```bash
   git commit -m "Add async file processing for large datasets

   - Implement AsyncFileProcessor class
   - Add thread pool execution for CPU-bound operations
   - Integrate with existing file processing pipeline
   - Add unit tests for async processing
   "
   ```

4. **Run Quality Checks**

   ```bash
   # Format code
   make format

   # Run linting
   make lint

   # Run tests
   make test
   ```

### 3. Submitting Changes

1. **Update Your Branch**

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to Your Fork**

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**

   - Use descriptive title and description
   - Reference related issues
   - Include testing instructions
   - Request review from maintainers

### Pull Request Guidelines

- **Title**: Clear, descriptive summary of changes
- **Description**: Detailed explanation of changes, motivation, and testing
- **Testing**: Describe how changes were tested
- **Breaking Changes**: Clearly mark any breaking changes
- **Documentation**: Confirm documentation updates are included

## Code Review Process

### Review Criteria

Pull requests are evaluated on:

1. **Functionality**: Does the code work as intended?
2. **Code Quality**: Adherence to coding standards and best practices
3. **Testing**: Adequate test coverage and test quality
4. **Documentation**: Appropriate documentation updates
5. **Performance**: No significant performance regressions
6. **Security**: No security vulnerabilities introduced

### Review Feedback

- Address all review comments
- Make requested changes or provide justification
- Update pull request as needed
- Respond to reviewer questions promptly

### Approval Process

- At least one maintainer approval required
- All CI checks must pass
- No unresolved review comments
- Documentation must be updated

## Release Process

### Version Numbering

The project follows Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Checklist

1. Update version numbers in `pyproject.toml` and `package.json`
2. Update `CHANGELOG.md` with release notes
3. Ensure all tests pass
4. Update documentation for any new features
5. Create release tag
6. Build and publish packages (if applicable)

## Development Tools

### Makefile Commands

```bash
# Development
make install          # Install dependencies
make setup           # Configure system
make start           # Start all services
make start-gateway   # Start gateway only
make start-backend   # Start backend only
make start-frontend  # Start frontend only

# Testing
make test            # Run all tests
make test-unit       # Unit tests only
make test-integration # Integration tests only

# Code Quality
make lint            # Run linters
make format          # Format code
make type-check      # Type checking

# Docker
make build-docker    # Build production images
make up              # Start production services
make down            # Stop services
make logs            # View logs
```

### Pre-commit Hooks

Pre-commit hooks automatically run:

- Black formatting check
- isort import sorting check
- flake8 style checking
- Basic pytest validation

## Troubleshooting

### Common Issues

**Import Errors**: Ensure virtual environment is activated and dependencies are installed.

**Test Failures**: Check that configuration is set up correctly and test data directories exist.

**Linting Errors**: Run `make format` to auto-fix formatting issues.

**Type Checking Errors**: Review type hints and ensure all imports have type stubs available.

## Getting Help

- **Documentation**: Check `documentation/` directory for detailed guides
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Contact**: Reach out to maintainers for critical issues

## Additional Resources

- [System Architecture Documentation](documentation/explanation/system-architecture.md)
- [API Reference](documentation/reference/api-endpoints.md)
- [Codebase Glossary](documentation/reference/codebase_glossary.md)
- [Testing Guide](documentation/how-to-guides/testing-the-codebase.md)

Thank you for contributing to MDJourney. Your efforts help advance FAIR data practices in scientific research.
