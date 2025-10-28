# FAIR Metadata Automation System

A comprehensive system for automating FAIR-compliant metadata capture and management for research data. The system provides automated file processing, schema-driven metadata generation, and a modern web interface for researchers to manage their data metadata efficiently.

## Features

### Core Functionality
- **Automated Metadata Generation** - Automatic creation of FAIR-compliant metadata files
- **Schema-Driven Validation** - Dynamic schema resolution with local override support
- **File System Monitoring** - Real-time detection and processing of new files
- **Version Control Integration** - Git and DVC integration for data and metadata versioning
- **Modern Web Interface** - React-based three-pane layout for intuitive metadata management

### Advanced Features
- **Dynamic Schema Resolution** - Support for local schema overrides and packaged defaults
- **File Upload System** - Upload files directly to datasets with automatic metadata tracking
- **Async Processing** - High-performance asynchronous file processing
- **Caching System** - Redis-based caching for improved performance
- **Security Features** - Input validation, rate limiting, and authentication
- **Docker Support** - Complete containerization for easy deployment
- **Comprehensive Testing** - Unit, integration, and stress testing suites

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git
- Docker (optional)
- DVC (optional)

### Installation & Setup

```bash
# Clone and setup
git clone <repository-url>
cd mdjourney-dev

# Install dependencies
make install

# Initial configuration
make setup
```

### Try the Decoupled Architecture (Remote backend + Local GUI)

Follow this recommended flow:

1. On the remote server (e.g., HPC), run one-time setup to point the monitor to the target directory:
   ```bash
   make setup
   ```
2. Start the backend on the remote server:
   ```bash
   make start-backend
   ```
3. On your local machine, set up an SSH tunnel to the remote backend:
   ```bash
   ssh -L 8000:localhost:8000 <username>@<server-host> -N
   # For KU Leuven HPC compute-node case, see documentation/how-to-guides/decoupled-architecture.md
   ```
4. Start the GUI locally in Docker:
   ```bash
   make up-frontend
   ```

For detailed guidance, see `documentation/how-to-guides/decoupled-architecture.md`.

### Development Commands

```bash
# Start the complete system (monitor + API + frontend)
make start

# Start individual components
make start-api      # API server only
make start-monitor  # File system monitor only
make start-frontend # Frontend development server only

# Testing
make test           # Run all tests
make test-unit      # Unit tests only
make test-integration # Integration tests only
make test-stress    # Stress tests only

# Code quality
make lint           # Run linters
make format         # Format code
make type-check     # Type checking

# Build & package
make build          # Build package
make clean          # Clean build artifacts
```

### Service URLs

When running the system:
- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Basic Workflow

1. **Create a project folder** with `p_` prefix
   ```bash
   mkdir data/p_MyResearchProject
   ```

2. **Create dataset folders** within the project with `d_` prefix
   ```bash
   mkdir data/p_MyResearchProject/d_dataset_RNAseq_rep1
   ```

3. **Add data files** - the system automatically detects and processes them

4. **Access the web interface** at http://localhost:5173 to view and edit metadata

### Configuration

The system uses a `.fair_meta_config.yaml` file for configuration. Run `make setup` to create this file.

## Architecture

### System Components

- **Backend API** (`api/`) - FastAPI-based REST API with comprehensive endpoints
- **Application Services** (`app/`) - Core business logic and services
- **Frontend** (`frontend/`) - React-based web interface with TypeScript
- **File Monitor** - Real-time file system monitoring and processing
- **Schema Management** - Dynamic schema resolution and validation

### Key Technologies

**Backend**:
- FastAPI for high-performance API
- Pydantic for data validation
- SQLAlchemy for database operations
- Redis for caching
- Celery for background tasks

**Frontend**:
- React 18 with TypeScript
- Material-UI for components
- TanStack Query for server state
- Zustand for client state
- Vite for fast builds

**Infrastructure**:
- Docker for containerization
- Nginx for load balancing
- Redis for caching and sessions
- Git/DVC for version control

## Documentation

Comprehensive documentation is available in the `documentation/` directory:

### Explanation
- **[System Architecture](documentation/explanation/system-architecture.md)** - Detailed system design and implementation
- **[Frontend Architecture](documentation/explanation/frontend-architecture.md)** - Frontend component architecture and patterns
- **[System Workflow](documentation/explanation/system-workflow.md)** - Complete workflow diagrams and processes
- **[Schema Resolution](documentation/explanation/schema-resolution.md)** - Dynamic schema resolution mechanism

### How-to Guides
- **[Configuration Management](documentation/how-to-guides/configuration-management.md)** - Comprehensive configuration guide
- **[Using Docker](documentation/how-to-guides/using-docker.md)** - Docker setup and deployment
- **[Testing the Codebase](documentation/how-to-guides/testing-the-codebase.md)** - Complete testing guide
- **[Contributing](documentation/how-to-guides/contributing.md)** - Development and contribution guidelines
- **[Performance Optimizations](documentation/how-to-guides/performance-optimizations.md)** - Performance tuning and optimization

### Reference
- **[API Endpoints](documentation/reference/api-endpoints.md)** - Complete API reference documentation
- **[Codebase Glossary](documentation/reference/codebase_glossary.md)** - Comprehensive component and concept reference

## API Reference

The system provides a comprehensive REST API with the following main endpoint categories:

### Discovery Endpoints
- `GET /api/v1/projects` - List all projects
- `GET /api/v1/projects/{project_id}/datasets` - List project datasets
- `POST /api/v1/rescan` - Trigger system rescan

### Schema Endpoints
- `GET /api/v1/schemas/contextual` - List contextual schemas
- `GET /api/v1/schemas/{schema_type}/{schema_id}` - Get specific schema

### Metadata Endpoints
- `GET /api/v1/datasets/{dataset_id}/metadata/{metadata_type}` - Get metadata
- `PUT /api/v1/datasets/{dataset_id}/metadata/{metadata_type}` - Update metadata

### Experiment Workflow
- `POST /api/v1/datasets/{dataset_id}/contextual` - Create contextual template
- `POST /api/v1/datasets/{dataset_id}/finalize` - Finalize dataset

### System Endpoints
- `GET /api/v1/health` - Health check
- `POST /api/v1/config/reload` - Reload configuration

## Testing

The system includes comprehensive testing at multiple levels:

### Test Types
- **Unit Tests** - Individual component testing with 90% coverage requirement
- **Integration Tests** - API and system integration testing
- **Regression Tests** - Stability and compatibility testing
- **Stress Tests** - Performance and load testing

### Running Tests
```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-stress

# Run with coverage
make test-coverage
```

## Deployment

### Docker Deployment

**Production**:
```bash
make build-docker
make up
```

**Development**:
```bash
make build-dev
make up-dev
```

### Environment Configuration

The system supports multiple deployment environments:
- **Development** - Hot reloading and debug features
- **Staging** - Production-like testing environment
- **Production** - Optimized for performance and security

## Security Features

- **Input Validation** - Comprehensive input sanitization
- **Path Traversal Protection** - Security against directory traversal attacks
- **Rate Limiting** - API abuse prevention
- **Authentication** - Optional API key authentication
- **Authorization** - Role-based access control
- **Security Headers** - HTTP security headers

## Performance

The system is optimized for high performance:
- **Async Processing** - Non-blocking file processing
- **Caching** - Redis-based caching for improved response times
- **Connection Pooling** - Database connection optimization
- **Code Splitting** - Frontend bundle optimization
- **Compression** - Response compression for reduced bandwidth

## Contributing

We welcome contributions! Please see our [Contributing Guide](documentation/how-to-guides/contributing.md) for:
- Development setup
- Coding standards
- Testing requirements
- Pull request process
- Code review guidelines

## Support

For detailed information, see the [Codebase Glossary](documentation/reference/codebase_glossary.md) and the [Contributing Guide](documentation/how-to-guides/contributing.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.
