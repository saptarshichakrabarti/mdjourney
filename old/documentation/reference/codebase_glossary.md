# FAIR Metadata Automation System - Codebase Glossary

This document provides a comprehensive reference for all components, modules, and concepts in the FAIR Metadata Automation System codebase.

## Table of Contents

- [Core Architecture](#core-architecture)
- [API Layer](#api-layer)
- [Application Services](#application-services)
- [Core Infrastructure](#core-infrastructure)
- [Frontend Components](#frontend-components)
- [Configuration & Setup](#configuration--setup)
- [Testing & Quality](#testing--quality)
- [Deployment & Operations](#deployment--operations)
- [Key Concepts](#key-concepts)

## Core Architecture

### System Overview

The FAIR Metadata Automation System is a comprehensive platform for automating FAIR-compliant metadata capture and management for research data. It consists of three main components:

1. **Backend API** (`api/`) - FastAPI-based REST API
2. **Application Services** (`app/`) - Core business logic and services
3. **Frontend** (`frontend/`) - React-based web interface

### Directory Structure

```
mdjourney-dev/
├── api/                    # FastAPI backend
├── app/                    # Core application services
├── frontend/              # React frontend
├── packaged_schemas/      # JSON schema definitions
├── documentation/         # System documentation
├── tests/                # Test suites
├── scripts/              # Utility scripts
└── docker-compose*.yml   # Container orchestration
```

## API Layer

### Main Application (`api/main.py`)

**Purpose**: FastAPI application entry point and route definitions

**Key Features**:
- CORS middleware configuration
- Security middleware with rate limiting
- Authentication and authorization
- Error handling and logging
- Health check endpoints

**Dependencies**:
- FastAPI framework
- Custom service dependencies
- Security and authentication modules

### API Routers

#### Project Service (`api/routers/project_service.py`)
**Purpose**: Handles project discovery and management operations

**Key Methods**:
- `list_projects()` - Scan and return all projects
- `list_project_datasets()` - Get datasets for a specific project
- `rescan_projects()` - Force refresh of project cache

#### Metadata Service (`api/routers/metadata_service.py`)
**Purpose**: Manages metadata CRUD operations and validation

**Key Methods**:
- `get_metadata()` - Retrieve metadata files
- `update_metadata()` - Save and validate metadata
- `create_contextual_template()` - Generate experiment templates
- `finalize_dataset()` - Create V2 complete metadata

#### Schema Service (`api/routers/schema_service.py`)
**Purpose**: Handles schema resolution and discovery

**Key Methods**:
- `list_contextual_schemas()` - Get available contextual schemas
- `get_schema()` - Retrieve specific schema content
- `resolve_schema_path()` - Implement schema resolution logic

### Data Models (`api/models/pydantic_models.py`)

**Purpose**: Pydantic models for API request/response validation

**Key Models**:
- `ProjectSummary` - Project information
- `DatasetSummary` - Dataset information
- `SchemaInfo` - Schema metadata
- `MetadataFile` - Metadata content with schema info
- `MetadataUpdatePayload` - Update request payload
- `ContextualTemplatePayload` - Template creation payload
- `FinalizePayload` - Dataset finalization payload

### Dependencies (`api/dependencies.py`)

**Purpose**: Dependency injection for API services

**Key Functions**:
- `get_project_service()` - Project service dependency
- `get_metadata_service()` - Metadata service dependency
- `get_schema_service()` - Schema service dependency

## Application Services

### Core Services (`app/services/`)

#### File Processor (`app/services/file_processor.py`)
**Purpose**: Handles file metadata extraction and processing

**Key Features**:
- Pluggable file scanner architecture
- Integration with dirmeta library
- Security validation and path sanitization
- Version control integration

**Key Methods**:
- `process_new_file()` - Extract metadata from new files
- `update_dataset_structural()` - Update structural metadata
- `validate_file_path()` - Security validation

#### Async File Processor (`app/services/async_file_processor.py`)
**Purpose**: Asynchronous version of file processing

**Key Features**:
- Async/await support for better performance
- Caching integration
- Background task processing
- Error handling and retry logic

#### Metadata Generator (`app/services/metadata_generator.py`)
**Purpose**: Generates and manages metadata files

**Key Methods**:
- `generate_project_file()` - Create project descriptive metadata
- `generate_dataset_files()` - Create dataset metadata files
- `create_experiment_contextual_template()` - Generate contextual templates
- `generate_complete_metadata_file()` - Create V2 complete metadata

#### Schema Manager (`app/services/schema_manager.py`)
**Purpose**: Manages JSON schema loading and validation

**Key Features**:
- Schema resolution (local override vs packaged default)
- Schema caching for performance
- Validation against JSON schemas
- Error handling and reporting

**Key Methods**:
- `load_schema()` - Load schema with resolution logic
- `validate_metadata()` - Validate against schema
- `get_schema_path()` - Resolve schema file path
- `list_contextual_schemas()` - Discover available schemas

#### Async Schema Manager (`app/services/async_schema_manager.py`)
**Purpose**: Asynchronous version of schema management

**Key Features**:
- Async schema loading
- Caching integration
- Background validation
- Performance optimization

#### Version Control Manager (`app/services/version_control.py`)
**Purpose**: Handles Git and DVC operations

**Key Methods**:
- `commit_metadata_changes()` - Git commit operations
- `add_data_file_to_dvc()` - DVC tracking
- `get_git_status()` - Check repository status
- `create_tag()` - Version tagging

#### File Scanners (`app/services/scanners.py`)
**Purpose**: Pluggable file scanning implementations

**Key Classes**:
- `IFileScanner` - Abstract base interface
- `DirmetaScanner` - dirmeta library integration
- `CustomScanner` - Custom scanning implementations

### Core Infrastructure (`app/core/`)

#### Configuration Management (`app/core/config.py`)
**Purpose**: Centralized configuration management

**Key Features**:
- Environment variable support
- Configuration validation
- Default value management
- Runtime configuration access

**Key Functions**:
- `initialize_config()` - Load configuration from file
- `get_config_value()` - Access configuration values
- `get_api_config()` - API-specific configuration
- `get_security_config()` - Security settings

#### Configuration Manager (`app/core/config_manager.py`)
**Purpose**: Advanced configuration management with environment support

**Key Features**:
- Environment-specific configurations
- Configuration validation
- Migration support
- Caching and reloading

**Key Methods**:
- `load_config()` - Load with environment overrides
- `validate_config()` - Validate configuration
- `get_setting()` - Access nested settings
- `reload_config()` - Clear cache and reload

#### Authentication (`app/core/auth.py`)
**Purpose**: Authentication and authorization system

**Key Features**:
- API key authentication
- Role-based access control (RBAC)
- User session management
- Permission checking

**Key Classes**:
- `APIKeyManager` - API key validation
- `RoleBasedAccessControl` - Permission management

**Key Functions**:
- `get_current_user()` - Get authenticated user
- `get_optional_user()` - Optional authentication
- `require_permission()` - Permission decorator

#### Security (`app/core/security.py`)
**Purpose**: Security utilities and middleware

**Key Features**:
- Input validation and sanitization
- Path traversal protection
- Security headers
- Rate limiting

**Key Classes**:
- `InputValidator` - Input validation
- `PathSanitizer` - Path security
- `SecurityHeaders` - HTTP security headers
- `rate_limiter` - Rate limiting decorator

#### Caching (`app/core/cache.py`)
**Purpose**: Caching system for performance optimization

**Key Features**:
- Redis integration
- In-memory caching
- Cache invalidation
- Performance monitoring

**Key Functions**:
- `cached()` - Caching decorator
- `get_metadata_cache()` - Metadata cache access
- `invalidate_cache()` - Cache invalidation

#### Performance (`app/core/performance.py`)
**Purpose**: Performance monitoring and optimization

**Key Features**:
- Performance metrics
- Profiling support
- Resource monitoring
- Optimization recommendations

#### Background Tasks (`app/core/background_tasks.py`)
**Purpose**: Background task processing

**Key Features**:
- Async task execution
- Task queuing
- Error handling
- Progress tracking

#### Exception Handling (`app/core/exceptions.py`)
**Purpose**: Custom exception classes and error handling

**Key Exceptions**:
- `MDJourneyError` - Base exception class
- `ResourceNotFoundError` - Resource not found
- `ValidationError` - Validation failures
- `SchemaNotFoundError` - Schema resolution errors
- `SecurityError` - Security violations
- `AuthenticationError` - Authentication failures
- `AuthorizationError` - Authorization failures

### Monitoring (`app/monitors/`)

#### Folder Monitor (`app/monitors/folder_monitor.py`)
**Purpose**: File system monitoring and event handling

**Key Features**:
- Real-time file system monitoring
- Event-driven processing
- Automatic metadata generation
- Error handling and recovery

**Key Classes**:
- `FolderCreationHandler` - File system event handler
- `FolderMonitor` - Main monitoring service

### Utilities (`app/utils/`)

#### Helpers (`app/utils/helpers.py`)
**Purpose**: Common utility functions

**Key Functions**:
- `calculate_checksum_incremental()` - File checksum calculation
- `get_current_timestamp()` - Timestamp utilities
- `sanitize_filename()` - Filename sanitization
- `validate_path()` - Path validation

## Frontend Components

### Main Application (`frontend/src/App.tsx`)
**Purpose**: Main React application component

**Key Features**:
- Three-pane layout (Project Browser, Metadata Editor, Context Panel)
- Theme management (light/dark mode)
- Error boundaries
- Responsive design

### Core Components

#### Project Browser (`frontend/src/components/ProjectBrowser.tsx`)
**Purpose**: Project and dataset navigation

**Key Features**:
- Project/dataset tree view
- Status indicators
- Auto-refresh functionality
- Selection management

#### Metadata Editor (`frontend/src/components/MetadataEditor.tsx`)
**Purpose**: Metadata editing interface

**Key Features**:
- Schema-driven form generation
- Real-time validation
- Save/load functionality
- Field status tracking

#### Schema-Driven Form (`frontend/src/components/SchemaDrivenForm.tsx`)
**Purpose**: Dynamic form generation from JSON schemas

**Key Features**:
- Automatic form field generation
- Type-specific input components
- Validation integration
- Field help and descriptions

#### Context Panel (`frontend/src/components/ContextPanel.tsx`)
**Purpose**: Contextual information and actions

**Key Features**:
- Field help display
- Validation error summary
- Action buttons
- Progress tracking

#### Navigation Panel (`frontend/src/components/NavigationPanel.tsx`)
**Purpose**: Form navigation and field jumping

**Key Features**:
- Form section navigation
- Field highlighting
- Progress indicators
- Quick access

### Supporting Components

#### Error Boundary (`frontend/src/components/ErrorBoundary.tsx`)
**Purpose**: Error handling and recovery

#### Loading Skeleton (`frontend/src/components/LoadingSkeleton.tsx`)
**Purpose**: Loading state management

#### Field Status Indicator (`frontend/src/components/FieldStatusIndicator.tsx`)
**Purpose**: Field validation status display

#### Progress Tracker (`frontend/src/components/ProgressTracker.tsx`)
**Purpose**: Progress visualization

### Services (`frontend/src/services/`)

#### API Service (`frontend/src/services/api.ts`)
**Purpose**: Backend API communication

**Key Features**:
- HTTP client configuration
- Request/response handling
- Error handling
- Type safety

**Key Methods**:
- `getProjects()` - Fetch projects
- `getProjectDatasets()` - Fetch datasets
- `getMetadata()` - Fetch metadata
- `updateMetadata()` - Save metadata
- `createContextualTemplate()` - Create templates
- `finalizeDataset()` - Finalize datasets

### State Management (`frontend/src/store/`)

#### App Store (`frontend/src/store/appStore.ts`)
**Purpose**: Global application state management

**Key Features**:
- Zustand-based state management
- Selection state
- UI state
- Cache management

### Hooks (`frontend/src/hooks/`)

#### App Theme (`frontend/src/hooks/useAppTheme.ts`)
**Purpose**: Theme management hook

#### Field Status (`frontend/src/hooks/useFieldStatus.ts`)
**Purpose**: Field validation status hook

#### Scroll Sync (`frontend/src/hooks/useScrollSync.ts`)
**Purpose**: Synchronized scrolling hook

### Utilities (`frontend/src/utils/`)

#### Form Analyzer (`frontend/src/utils/formAnalyzer.ts`)
**Purpose**: Form analysis and validation

#### Schema Utils (`frontend/src/utils/schemaUtils.ts`)
**Purpose**: Schema processing utilities

### Types (`frontend/src/types/`)

#### API Types (`frontend/src/types/api.ts`)
**Purpose**: TypeScript type definitions for API communication

## Configuration & Setup

### Environment Configuration

#### Environment Variables
- `MDJOURNEY_ENV` - Environment name (development, staging, production)
- `MONITOR_PATH` - Path to monitor directory
- `LOG_LEVEL` - Logging level
- `API_HOST` - API server host
- `API_PORT` - API server port
- `CORS_ORIGINS` - Allowed CORS origins
- `MDJOURNEY_API_KEY` - API authentication key
- `DATABASE_URL` - Database connection URL
- `REDIS_HOST` - Redis server host
- `REDIS_PORT` - Redis server port

#### Configuration Files
- `.fair_meta_config.yaml` - Main configuration file
- `configs/development.yaml` - Development environment config
- `configs/staging.yaml` - Staging environment config
- `configs/production.yaml` - Production environment config

### Schema Management

#### Packaged Schemas (`packaged_schemas/`)
- `project_descriptive.json` - Project-level metadata schema
- `dataset_administrative_schema.json` - Dataset administrative schema
- `dataset_structural_schema.json` - Dataset structural schema
- `experiment_contextual_schema.json` - Experiment contextual schema
- `instrument_technical_schema.json` - Instrument technical schema
- `complete_metadata_schema.json` - Complete metadata schema
- `fair_meta_config_template.yaml` - Configuration template

#### Contextual Schemas (`packaged_schemas/contextual/`)
- `genomics_sequencing.json` - Genomics sequencing schema
- `microscopy_imaging.json` - Microscopy imaging schema
- `annmudata.json` - ANNMU data schema

## Testing & Quality

### Test Structure (`tests/`)

#### Unit Tests (`tests/unit/`)
- `test_basic_functionality.py` - Core functionality tests
- `test_metadata_generator.py` - Metadata generation tests
- `test_schema_manager.py` - Schema management tests

#### Integration Tests (`tests/integration/`)
- `test_api_endpoints.py` - API endpoint tests
- `test_system_integration.py` - System integration tests

#### Regression Tests (`tests/regression/`)
- `test_basic_regression.py` - Regression test suite

#### Stress Tests (`tests/stress_tests/`)
- `api_stresser.py` - API stress testing
- `file_stresser.py` - File processing stress tests
- `run_suite.py` - Stress test orchestration
- `generate_report.py` - Test report generation

### Quality Assurance

#### Linting (`scripts/lint.py`)
**Purpose**: Code quality and style checking

#### Configuration Validation (`scripts/validate_config.py`)
**Purpose**: Configuration file validation

#### Process Management (`scripts/process_manager.py`)
**Purpose**: Process monitoring and management

## Deployment & Operations

### Docker Configuration

#### Production (`docker-compose.yml`)
- Optimized for production deployment
- Frontend served via nginx
- Health checks enabled
- Minimal volume mounts

#### Development (`docker-compose.dev.yml`)
- Hot reloading enabled
- Volume mounts for live code changes
- Development tools included
- Debug logging enabled

### Dockerfiles
- `Dockerfile.api` - API service container
- `Dockerfile.api.prod` - Production API container
- `Dockerfile.monitor` - Monitor service container
- `frontend/Dockerfile` - Frontend container
- `frontend/Dockerfile.dev` - Development frontend container

### Makefile Commands
- `make install` - Install dependencies
- `make setup` - Initial configuration
- `make start` - Start complete system
- `make build-docker` - Build production images
- `make up` - Start production services
- `make test` - Run test suite
- `make lint` - Run linting
- `make clean` - Clean build artifacts

## Key Concepts

### FAIR Principles
- **Findability**: Metadata enables discovery
- **Accessibility**: Metadata is retrievable
- **Interoperability**: Metadata uses standard formats
- **Reusability**: Metadata enables reuse

### Metadata Categories
1. **Project Descriptive**: High-level project context
2. **Dataset Administrative**: Dataset lifecycle and management
3. **Dataset Structural**: Dataset organization and files
4. **Instrument Technical**: Instrument specifications
5. **Experiment Contextual**: Experiment-specific details
6. **File Technical**: File-level technical metadata

### Schema Resolution Principle
The system implements a two-tier schema resolution:
1. **Local Override**: Check for local schemas in `.template_schemas/`
2. **Packaged Default**: Fall back to packaged schemas

### Version Control Integration
- **Git**: Metadata file versioning
- **DVC**: Data file versioning
- **Automated Commits**: Automatic version control operations

### File System Monitoring
- **Real-time Monitoring**: File system event detection
- **Automatic Processing**: Trigger-based metadata generation
- **Error Recovery**: Robust error handling and recovery

### Security Features
- **Input Validation**: Comprehensive input sanitization
- **Path Traversal Protection**: Security against directory traversal
- **Rate Limiting**: API abuse prevention
- **Authentication**: Optional API key authentication
- **Authorization**: Role-based access control

### Performance Optimization
- **Caching**: Redis and in-memory caching
- **Async Processing**: Asynchronous file processing
- **Background Tasks**: Non-blocking operations
- **Schema Caching**: Schema loading optimization

### Error Handling
- **Custom Exceptions**: Comprehensive exception hierarchy
- **Error Recovery**: Automatic error recovery mechanisms
- **Logging**: Comprehensive logging system
- **User Feedback**: Clear error messages and guidance

This glossary provides a comprehensive reference for understanding the FAIR Metadata Automation System codebase. Each component is designed to work together to provide a robust, scalable, and maintainable platform for FAIR-compliant metadata management.