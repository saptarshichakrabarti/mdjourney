# Testing the Codebase

This document provides comprehensive guidance on testing the FAIR Metadata Automation System, covering unit tests, integration tests, stress tests, and quality assurance procedures.

## Testing Overview

The testing strategy for the FAIR Metadata Automation System is designed to ensure reliability, performance, and maintainability across all components. The test suite includes:

- **Unit Tests** - Individual component testing
- **Integration Tests** - Component interaction testing
- **Regression Tests** - Stability and compatibility testing
- **Stress Tests** - Performance and load testing
- **Quality Assurance** - Code quality and style checking

## Test Structure

### Directory Organization

```
tests/
├── unit/                    # Unit tests
│   ├── test_basic_functionality.py
│   ├── test_metadata_generator.py
│   └── test_schema_manager.py
├── integration/             # Integration tests
│   ├── test_api_endpoints.py
│   └── test_system_integration.py
├── regression/             # Regression tests
│   └── test_basic_regression.py
├── stress_tests/           # Stress and performance tests
│   ├── api_stresser.py
│   ├── file_stresser.py
│   ├── run_suite.py
│   ├── generate_report.py
│   └── logger_config.py
├── fixtures/               # Test data and fixtures
│   └── test_data.py
├── conftest.py            # Pytest configuration
└── run_tests.py           # Test runner script
```

## Unit Testing

### Test Framework

**Framework**: pytest with custom fixtures and plugins

**Key Features**:
- Fixture-based test setup
- Parameterized testing
- Mock and patch support
- Coverage reporting
- Parallel test execution

### Core Unit Tests

#### Basic Functionality Tests (`tests/unit/test_basic_functionality.py`)

**Purpose**: Test core system functionality

**Test Categories**:
- Configuration loading and validation
- File system operations
- Utility function testing
- Error handling verification

**Key Test Cases**:
```python
def test_config_initialization():
    """Test configuration loading from file"""

def test_file_path_validation():
    """Test file path security validation"""

def test_checksum_calculation():
    """Test file checksum calculation"""

def test_timestamp_generation():
    """Test timestamp utility functions"""
```

#### Metadata Generator Tests (`tests/unit/test_metadata_generator.py`)

**Purpose**: Test metadata generation functionality

**Test Categories**:
- Project metadata generation
- Dataset metadata generation
- Contextual template creation
- V2 complete metadata generation

**Key Test Cases**:
```python
def test_generate_project_file():
    """Test project descriptive metadata generation"""

def test_generate_dataset_files():
    """Test dataset metadata file generation"""

def test_create_contextual_template():
    """Test experiment contextual template creation"""

def test_generate_complete_metadata():
    """Test V2 complete metadata generation"""
```

#### Schema Manager Tests (`tests/unit/test_schema_manager.py`)

**Purpose**: Test schema management and validation

**Test Categories**:
- Schema loading and resolution
- Validation against schemas
- Local override handling
- Error handling and reporting

**Key Test Cases**:
```python
def test_schema_loading():
    """Test schema loading from packaged defaults"""

def test_local_schema_override():
    """Test local schema override resolution"""

def test_metadata_validation():
    """Test metadata validation against schemas"""

def test_schema_caching():
    """Test schema caching performance"""
```

### Running Unit Tests

```bash
# Run all unit tests
make test-unit

# Run specific test file
pytest tests/unit/test_metadata_generator.py

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=html

# Run with verbose output
pytest tests/unit/ -v

# Run specific test case
pytest tests/unit/test_schema_manager.py::test_schema_loading
```

## Integration Testing

### Integration Test Framework

**Framework**: pytest with FastAPI test client

**Key Features**:
- API endpoint testing
- Database integration testing
- File system integration testing
- End-to-end workflow testing

### API Endpoint Tests (`tests/integration/test_api_endpoints.py`)

**Purpose**: Test API endpoints and their interactions

**Test Categories**:
- Discovery endpoints
- Schema endpoints
- Metadata CRUD operations
- Experiment workflow endpoints
- Error handling and validation

**Key Test Cases**:
```python
def test_list_projects():
    """Test project listing endpoint"""

def test_get_project_datasets():
    """Test dataset listing for project"""

def test_get_metadata():
    """Test metadata retrieval"""

def test_update_metadata():
    """Test metadata update and validation"""

def test_create_contextual_template():
    """Test contextual template creation"""

def test_finalize_dataset():
    """Test dataset finalization"""
```

### System Integration Tests (`tests/integration/test_system_integration.py`)

**Purpose**: Test complete system workflows

**Test Categories**:
- End-to-end metadata workflows
- File system monitoring integration
- Version control integration
- Error recovery and resilience

**Key Test Cases**:
```python
def test_complete_metadata_workflow():
    """Test complete metadata creation workflow"""

def test_file_monitoring_integration():
    """Test file system monitoring integration"""

def test_version_control_integration():
    """Test Git/DVC integration"""

def test_error_recovery():
    """Test system error recovery"""
```

### Running Integration Tests

```bash
# Run all integration tests
make test-integration

# Run with API server
pytest tests/integration/ --api-server

# Run specific integration test
pytest tests/integration/test_api_endpoints.py

# Run with database
pytest tests/integration/ --database
```

## Regression Testing

### Regression Test Suite (`tests/regression/test_basic_regression.py`)

**Purpose**: Ensure system stability and backward compatibility

**Test Categories**:
- Backward compatibility testing
- Configuration migration testing
- Schema evolution testing
- Performance regression testing

**Key Test Cases**:
```python
def test_backward_compatibility():
    """Test backward compatibility with old configurations"""

def test_schema_migration():
    """Test schema migration and evolution"""

def test_performance_regression():
    """Test for performance regressions"""

def test_data_migration():
    """Test data migration procedures"""
```

### Running Regression Tests

```bash
# Run regression tests
make test-regression

# Run with specific version
pytest tests/regression/ --version=1.0.0

# Run compatibility tests
pytest tests/regression/ --compatibility
```

## Stress Testing

### Stress Test Framework

**Framework**: Custom stress testing framework with reporting

**Key Features**:
- API load testing
- File processing stress testing
- Memory and resource monitoring
- Performance metrics collection
- Automated report generation

### API Stress Testing (`tests/stress_tests/api_stresser.py`)

**Purpose**: Test API performance under load

**Test Categories**:
- Concurrent request handling
- Rate limiting validation
- Memory usage under load
- Response time analysis
- Error rate monitoring

**Key Test Cases**:
```python
def test_concurrent_requests():
    """Test concurrent API request handling"""

def test_rate_limiting():
    """Test rate limiting under load"""

def test_memory_usage():
    """Test memory usage under stress"""

def test_response_times():
    """Test response time degradation"""
```

### File Processing Stress Tests (`tests/stress_tests/file_stresser.py`)

**Purpose**: Test file processing performance

**Test Categories**:
- Large file processing
- Concurrent file processing
- Memory usage during processing
- Processing time analysis
- Error handling under load

**Key Test Cases**:
```python
def test_large_file_processing():
    """Test processing of large files"""

def test_concurrent_file_processing():
    """Test concurrent file processing"""

def test_memory_efficiency():
    """Test memory efficiency during processing"""

def test_processing_performance():
    """Test processing performance metrics"""
```

### Stress Test Suite (`tests/stress_tests/run_suite.py`)

**Purpose**: Orchestrate comprehensive stress testing

**Features**:
- Test suite orchestration
- Resource monitoring
- Performance metrics collection
- Automated report generation
- Test result analysis

### Running Stress Tests

```bash
# Run complete stress test suite
make test-stress

# Run specific stress test
python tests/stress_tests/api_stresser.py

# Run with custom parameters
python tests/stress_tests/run_suite.py --duration=300 --concurrency=50

# Generate stress test report
python tests/stress_tests/generate_report.py
```

## Quality Assurance

### Code Quality Tools

#### Linting (`scripts/lint.py`)

**Purpose**: Code quality and style checking

**Tools Used**:
- **flake8** - Python code style checking
- **black** - Code formatting
- **isort** - Import sorting
- **mypy** - Type checking
- **pylint** - Advanced code analysis

**Running Linting**:
```bash
# Run all linting checks
make lint

# Run specific linter
flake8 app/ api/
black --check app/ api/
mypy app/ api/
```

#### Configuration Validation (`scripts/validate_config.py`)

**Purpose**: Configuration file validation

**Features**:
- Configuration syntax validation
- Environment variable checking
- Configuration completeness verification
- Migration compatibility testing

**Running Validation**:
```bash
# Validate configuration
python scripts/validate_config.py --config .fair_meta_config.yaml

# Validate with environment
python scripts/validate_config.py --config .fair_meta_config.yaml --environment production

# Check environment variables
python scripts/validate_config.py --config .fair_meta_config.yaml --check-env
```

### Test Data Management

#### Test Fixtures (`tests/fixtures/test_data.py`)

**Purpose**: Centralized test data management

**Features**:
- Sample project data
- Test metadata files
- Mock file structures
- Test configuration files

**Usage**:
```python
from tests.fixtures.test_data import sample_project, test_metadata

def test_with_sample_data():
    project = sample_project()
    metadata = test_metadata()
    # Test implementation
```

## Test Configuration

### Pytest Configuration (`tests/conftest.py`)

**Purpose**: Global test configuration and fixtures

**Key Features**:
- Global fixtures setup
- Test environment configuration
- Mock services configuration
- Test data initialization

### Test Runner (`tests/run_tests.py`)

**Purpose**: Comprehensive test execution

**Features**:
- Test suite orchestration
- Coverage reporting
- Test result aggregation
- Performance metrics collection

## Continuous Integration

### CI/CD Integration

**GitHub Actions Workflow**:
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: make install
      - name: Run tests
        run: make test
      - name: Run linting
        run: make lint
      - name: Generate coverage report
        run: make test-coverage
```

### Test Reporting

**Coverage Reports**:
- HTML coverage reports
- Coverage threshold enforcement
- Coverage trend analysis
- Missing coverage identification

**Performance Reports**:
- Response time analysis
- Memory usage tracking
- Resource utilization monitoring
- Performance regression detection

## Best Practices

### Test Development

1. **Test Isolation**: Each test should be independent
2. **Clear Naming**: Use descriptive test names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Data Management**: Use fixtures for consistent test data

### Test Maintenance

1. **Regular Updates**: Keep tests current with code changes
2. **Test Refactoring**: Refactor tests for maintainability
3. **Performance Monitoring**: Monitor test execution time
4. **Coverage Tracking**: Maintain high test coverage
5. **Documentation**: Document test purposes and scenarios

### Debugging Tests

1. **Verbose Output**: Use `-v` flag for detailed output
2. **Debug Mode**: Use `--pdb` for interactive debugging
3. **Test Isolation**: Run individual tests for debugging
4. **Logging**: Enable debug logging in tests
5. **Mock Verification**: Verify mock interactions

## Troubleshooting

### Common Issues

1. **Test Failures**: Check test data and environment setup
2. **Slow Tests**: Optimize test data and mock usage
3. **Flaky Tests**: Ensure test isolation and stability
4. **Coverage Issues**: Add tests for uncovered code paths
5. **Performance Issues**: Monitor resource usage and optimize

### Debug Commands

```bash
# Run tests with debug output
pytest tests/ -v --tb=long

# Run specific test with debugging
pytest tests/unit/test_schema_manager.py::test_schema_loading --pdb

# Check test coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run tests with performance profiling
pytest tests/ --profile
```

This comprehensive testing guide ensures the FAIR Metadata Automation System maintains high quality, reliability, and performance across all components and use cases.