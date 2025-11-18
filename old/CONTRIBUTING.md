# Contributing to FAIR Metadata Automation System

This guide provides comprehensive information for contributors to the FAIR Metadata Automation System, including development setup, coding standards, testing requirements, and contribution workflow.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Contribution Workflow](#contribution-workflow)
- [Code Review Process](#code-review-process)
- [Release Process](#release-process)

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.8+** - Core development language
- **Node.js 18+** - Frontend development
- **Git** - Version control
- **Docker** - Container development (optional)
- **DVC** - Data version control (optional)

### Repository Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/saptarshichakrabarti/mdjourney.git
   cd mdjourney-dev
   ```

2. **Set Up Remote**
   ```bash
   # Add upstream remote
   git remote add upstream https://github.com/saptarshichakrabarti/mdjourney.git

   # Verify remotes
   git remote -v
   ```

3. **Install Dependencies**
   ```bash
   # Install Python dependencies
   make install

   # Install frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

4. **Initial Configuration**
   ```bash
   # Create configuration file
   make setup

   # Validate configuration
   python scripts/validate_config.py --config .fair_meta_config.yaml
   ```

## Development Environment

### Backend Development

#### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

#### Development Commands

```bash
# Start API server in development mode
make start-api

# Start file monitor
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

#### IDE Configuration

**VS Code Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Frontend Development

#### Environment Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Development Commands

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Run linting
npm run lint

# Run type checking
npm run type-check

# Run tests
npm run test
```

#### IDE Configuration

**VS Code Extensions**:
- ES7+ React/Redux/React-Native snippets
- TypeScript Importer
- Prettier - Code formatter
- ESLint

## Coding Standards

### Python Standards

#### Code Style

**Formatting**: Black with line length of 88 characters
```python
# Good
def process_metadata_file(file_path: str, validate: bool = True) -> Dict[str, Any]:
    """Process metadata file with optional validation."""
    pass

# Bad
def process_metadata_file(file_path:str,validate:bool=True)->Dict[str,Any]:
    pass
```

**Import Organization**: isort with specific configuration
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local imports
from app.core.config import get_config_value
from app.services.metadata_generator import MetadataGenerator
```

**Type Hints**: Comprehensive type annotations
```python
from typing import Dict, List, Optional, Union, Any

def process_files(
    file_paths: List[str],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Union[str, int]]:
    """Process multiple files with optional configuration."""
    pass
```

#### Documentation Standards

**Docstrings**: Google style docstrings
```python
def generate_metadata(
    project_id: str,
    dataset_id: str,
    metadata_type: str
) -> Dict[str, Any]:
    """Generate metadata for a specific dataset.

    Args:
        project_id: Unique identifier for the project
        dataset_id: Unique identifier for the dataset
        metadata_type: Type of metadata to generate

    Returns:
        Dictionary containing generated metadata

    Raises:
        ValidationError: If input parameters are invalid
        SchemaNotFoundError: If required schema is not found

    Example:
        >>> metadata = generate_metadata("p_001", "d_001", "administrative")
        >>> print(metadata["dataset_title"])
    """
    pass
```

**Comments**: Clear, concise comments for complex logic
```python
# Calculate checksum using incremental reading to handle large files
def calculate_checksum_incremental(file_path: str) -> str:
    """Calculate SHA256 checksum for large files."""
    # Use chunked reading to avoid memory issues
    chunk_size = 4096
    # ... implementation
```

#### Error Handling

**Custom Exceptions**: Use specific exception types
```python
from app.core.exceptions import ValidationError, ResourceNotFoundError

def validate_dataset_id(dataset_id: str) -> None:
    """Validate dataset ID format."""
    if not dataset_id or not dataset_id.startswith("d_"):
        raise ValidationError(f"Invalid dataset ID format: {dataset_id}")
```

**Error Messages**: Clear, actionable error messages
```python
# Good
raise ResourceNotFoundError(
    f"Dataset '{dataset_id}' not found in project '{project_id}'"
)

# Bad
raise Exception("Error")
```

### Frontend Standards

#### TypeScript Standards

**Type Definitions**: Comprehensive type coverage
```typescript
interface ProjectSummary {
  project_id: string;
  project_title: string | null;
  path: string;
  dataset_count: number;
}

interface MetadataUpdatePayload {
  content: Record<string, unknown>;
}
```

**Component Structure**: Consistent component organization
```typescript
import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';

interface ComponentProps {
  title: string;
  onUpdate: (value: string) => void;
}

const Component: React.FC<ComponentProps> = ({ title, onUpdate }) => {
  const [value, setValue] = useState<string>('');

  useEffect(() => {
    // Effect logic
  }, [title]);

  const handleChange = (newValue: string) => {
    setValue(newValue);
    onUpdate(newValue);
  };

  return (
    <Box>
      <Typography variant="h6">{title}</Typography>
      {/* Component content */}
    </Box>
  );
};

export default Component;
```

#### React Standards

**Hooks Usage**: Consistent hook patterns
```typescript
// Custom hooks for reusable logic
const useMetadata = (datasetId: string, metadataType: string) => {
  const [metadata, setMetadata] = useState<MetadataFile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setLoading(true);
        const data = await APIService.getMetadata(datasetId, metadataType);
        setMetadata(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();
  }, [datasetId, metadataType]);

  return { metadata, loading, error };
};
```

**State Management**: Consistent state patterns
```typescript
// Zustand store patterns
interface AppState {
  selectedProjectId: string | null;
  selectedDatasetId: string | null;
  setSelectedProject: (id: string | null) => void;
  setSelectedDataset: (id: string | null) => void;
}

const useAppStore = create<AppState>((set) => ({
  selectedProjectId: null,
  selectedDatasetId: null,
  setSelectedProject: (id) => set({ selectedProjectId: id }),
  setSelectedDataset: (id) => set({ selectedDatasetId: id }),
}));
```

## Testing Requirements

### Test Coverage

**Minimum Coverage Requirements**:
- **Unit Tests**: 90% line coverage
- **Integration Tests**: 80% API endpoint coverage
- **Critical Paths**: 100% coverage for core functionality

### Test Development

**Unit Test Structure**:
```python
import pytest
from unittest.mock import Mock, patch
from app.services.metadata_generator import MetadataGenerator

class TestMetadataGenerator:
    """Test suite for MetadataGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create MetadataGenerator instance for testing."""
        return MetadataGenerator()

    def test_generate_project_file_success(self, generator):
        """Test successful project file generation."""
        # Arrange
        project_id = "p_test_project"
        expected_path = f"/data/{project_id}/.metadata/project_descriptive.json"

        # Act
        with patch('app.services.metadata_generator.Path.exists', return_value=True):
            result = generator.generate_project_file(project_id)

        # Assert
        assert result is not None
        assert "project_id" in result
        assert result["project_id"] == project_id

    def test_generate_project_file_invalid_id(self, generator):
        """Test project file generation with invalid ID."""
        # Arrange
        invalid_id = "invalid_project_id"

        # Act & Assert
        with pytest.raises(ValidationError):
            generator.generate_project_file(invalid_id)
```

**Integration Test Structure**:
```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_list_projects_success(self, client):
        """Test successful project listing."""
        # Arrange
        with patch('api.routers.project_service.ProjectService.list_projects') as mock_list:
            mock_list.return_value = [{"project_id": "p_test", "dataset_count": 0}]

            # Act
            response = client.get("/api/v1/projects")

            # Assert
            assert response.status_code == 200
            assert len(response.json()) == 1
            assert response.json()[0]["project_id"] == "p_test"
```

### Frontend Testing

**Component Testing**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProjectBrowser from '../components/ProjectBrowser';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

describe('ProjectBrowser', () => {
  it('renders project list correctly', () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectBrowser />
      </QueryClientProvider>
    );

    expect(screen.getByText('Projects')).toBeInTheDocument();
  });

  it('handles project selection', () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectBrowser />
      </QueryClientProvider>
    );

    const projectButton = screen.getByText('Test Project');
    fireEvent.click(projectButton);

    expect(projectButton).toHaveClass('selected');
  });
});
```

## Documentation Standards

### Code Documentation

**API Documentation**: Comprehensive API documentation
```python
@app.get("/api/v1/projects/{project_id}/datasets", response_model=List[DatasetSummary])
async def list_project_datasets(
    project_id: str = Path(..., description="The ID of the project"),
    project_service: ProjectService = Depends(get_project_service),
) -> List[DatasetSummary]:
    """List all datasets within a specific project.

    This endpoint scans a project folder and returns a summary for each dataset.
    The response includes dataset metadata status and basic information.

    Args:
        project_id: Unique identifier for the project (must start with 'p_')
        project_service: Injected project service dependency

    Returns:
        List of dataset summaries with metadata status

    Raises:
        HTTPException: 404 if project not found, 500 for server errors

    Example:
        GET /api/v1/projects/p_my_project/datasets
        Response: [{"dataset_id": "d_001", "status": "V1_Ingested"}]
    """
    pass
```

**README Updates**: Keep README files current
```markdown
## New Feature: Enhanced Metadata Validation

### Overview
Added comprehensive metadata validation with real-time feedback.

### Usage
```python
from app.services.metadata_generator import MetadataGenerator

generator = MetadataGenerator()
result = generator.validate_metadata(metadata_content, schema_type)
```

### Configuration
Add to `.fair_meta_config.yaml`:
```yaml
validation:
  strict_mode: true
  real_time_validation: true
```
```

### Documentation Updates

**When to Update Documentation**:
- New features or components
- API changes or additions
- Configuration changes
- Breaking changes
- Bug fixes with user impact

**Documentation Types**:
- **Code Comments**: Inline documentation
- **API Documentation**: Endpoint documentation
- **User Guides**: How-to documentation
- **Architecture Docs**: System design documentation
- **README Files**: Project overview and setup

## Contribution Workflow

### Branch Strategy

**Branch Naming Convention**:
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates
- `test/description` - Test improvements

**Example**:
```bash
git checkout -b feature/enhanced-metadata-validation
git checkout -b bugfix/fix-schema-resolution
git checkout -b docs/update-api-documentation
```

### Commit Standards

**Commit Message Format**:
```
type(scope): description

Detailed description of changes

Fixes #issue_number
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

**Examples**:
```bash
git commit -m "feat(api): add metadata validation endpoint

Add comprehensive metadata validation with schema checking
and real-time feedback capabilities.

Fixes #123"

git commit -m "fix(schema): resolve local override priority

Fix schema resolution to properly prioritize local overrides
over packaged defaults.

Fixes #456"
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following standards
   - Add comprehensive tests
   - Update documentation
   - Run quality checks

3. **Quality Checks**
   ```bash
   # Run tests
   make test

   # Run linting
   make lint

   # Check types
   make type-check

   # Validate configuration
   python scripts/validate_config.py --config .fair_meta_config.yaml
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(component): add new feature"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #issue_number
```

## Code Review Process

### Review Criteria

**Code Quality**:
- Follows coding standards
- Proper error handling
- Comprehensive testing
- Clear documentation

**Functionality**:
- Meets requirements
- Handles edge cases
- Performance considerations
- Security implications

**Maintainability**:
- Clear code structure
- Appropriate abstractions
- Reusable components
- Future extensibility

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs
   - Tests pass
   - Linting passes
   - Type checking passes

2. **Manual Review**
   - Code quality assessment
   - Functionality verification
   - Documentation review
   - Security review

3. **Approval Process**
   - At least one approval required
   - All comments addressed
   - CI checks pass
   - Ready for merge

### Review Guidelines

**For Reviewers**:
- Be constructive and specific
- Focus on code quality and functionality
- Suggest improvements, not just problems
- Test the changes locally when possible

**For Authors**:
- Respond to all comments
- Make requested changes
- Explain complex decisions
- Update documentation as needed

## Release Process

### Version Management

**Semantic Versioning**: `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

**Version Examples**:
- `1.0.0` - Initial release
- `1.1.0` - New features
- `1.1.1` - Bug fixes
- `2.0.0` - Breaking changes

### Release Workflow

1. **Prepare Release**
   ```bash
   # Update version numbers
   # Update CHANGELOG.md
   # Update documentation
   ```

2. **Create Release Branch**
```bash
   git checkout -b release/v1.1.0
   git push origin release/v1.1.0
   ```

3. **Release Testing**
```bash
   # Run full test suite
   make test

   # Run integration tests
   make test-integration

   # Run stress tests
   make test-stress
```

4. **Create Release**
```bash
   # Create GitHub release
   # Tag version
   # Generate release notes
   ```

### Changelog Management

**CHANGELOG.md Format**:
```markdown
## [1.1.0] - 2024-01-15

### Added
- Enhanced metadata validation
- Real-time validation feedback
- New API endpoints for schema management

### Changed
- Improved error handling in metadata generation
- Updated configuration format

### Fixed
- Fixed schema resolution priority
- Resolved memory leak in file processing

### Security
- Enhanced input validation
- Improved path sanitization
```

## Getting Help

### Resources

- **Documentation**: `documentation/` directory
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Code Review**: Pull request comments

### Contact

- **Maintainers**: @maintainer-username
- **Email**: project@example.com
- **Slack**: #fair-metadata-automation

### Contributing Guidelines

1. **Read Documentation**: Understand the system before contributing
2. **Follow Standards**: Adhere to coding and documentation standards
3. **Test Thoroughly**: Ensure all tests pass and add new tests
4. **Document Changes**: Update documentation for all changes
5. **Be Patient**: Allow time for review and feedback

Thank you for contributing to the FAIR Metadata Automation System!