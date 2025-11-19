# MDJourney - FAIR Metadata Automation System

MDJourney is an automated system designed to facilitate the creation and management of FAIR-compliant (Findable, Accessible, Interoperable, Reusable) metadata for research data. The system operates on a folder-driven paradigm, automatically capturing technical metadata while providing an intuitive web interface for researchers to complete contextual and administrative metadata.

## Overview

MDJourney employs a session-based gateway architecture that enables flexible deployment scenarios, from local development environments to distributed high-performance computing (HPC) infrastructures. The system monitors designated directory structures, automatically generating metadata templates when projects and datasets are created, and capturing file-level technical metadata as data files are added.

### Key Concepts

- **Automation First**: The system automatically captures technical details including file sizes, formats, checksums, and structural metadata, minimizing manual data entry requirements.
- **Folder-Driven Architecture**: Directory structure conventions dictate metadata organization, with project folders prefixed with `p_` and dataset folders prefixed with `d_`.
- **Metadata Storage**: MDJourney creates hidden `.metadata` subdirectories alongside data directories to store JSON metadata files. These directories are automatically managed by the system and should not be manually edited.
- **Session-Based Backend Management**: The gateway architecture enables per-session backend instances, allowing multiple users to work with different configurations simultaneously.

## System Architecture

The refactored MDJourney system consists of three primary components:

1. **Gateway Service** (`mdjourney-gateway/`): A FastAPI-based service that manages user sessions and routes requests to appropriate backend instances. The gateway handles session initialization, configuration management, and request proxying.

2. **Backend Service** (`mdjourney-backend/`): A FastAPI application providing the core metadata management functionality, including file system monitoring, metadata generation, schema validation, and version control integration.

3. **Web Application** (`mdjourney-webapp/`): A React-based frontend interface built with TypeScript and Material-UI, providing researchers with an intuitive interface for metadata entry and dataset management.

## Prerequisites

- **Python 3.8+**: Required for backend and gateway services
- **Node.js 18+**: Required for frontend development (optional if using Docker)
- **Docker and Docker Compose**: Recommended for containerized deployment
- **Git**: Required for version control integration
- **DVC**: Optional, for data version control

## Installation

### Quick Start with Docker

The recommended installation method uses Docker Compose for containerized deployment:

```bash
# Clone the repository
git clone https://github.com/saptarshichakrabarti/mdjourney.git
cd mdjourney-refactored

# Build and start all services
docker-compose up --build
```

This will start the gateway service on port 8080, backend services on port 8000, and the frontend on port 8080 (production) or 5173 (development).

### Manual Installation

For development or non-containerized deployment:

```bash
# Install backend dependencies
cd mdjourney-backend
pip install -r requirements.txt

# Install gateway dependencies
cd ../mdjourney-gateway
pip install -r requirements.txt

# Install frontend dependencies
cd ../mdjourney-webapp
npm install
```

## Configuration

Before starting the system, configuration must be established. The system uses YAML configuration files that follow the structure defined in `mdjourney-backend/packaged_schemas/fair_meta_config_template.yaml`.

### Initial Configuration Setup

**Important**: Configuration must be set up before starting services. Run the interactive configuration setup:

```bash
# From the root directory
make setup
```

Or manually:

```bash
cd mdjourney-backend
python scripts/setup_config.py
```

This will prompt for:
- Monitor path: The directory to watch for file system events (use absolute path)
- Custom schema path: Optional directory containing custom schema overrides
- Environment: Development, staging, or production
- API port: Port for the backend API server

This creates `.fair_meta_config.yaml` in the root directory. Alternatively, create a configuration file manually using `sample-config.yaml` as a template and rename it to `.fair_meta_config.yaml`.

### Configuration File Structure

The configuration file (`.fair_meta_config.yaml`) contains the following sections:

- **monitor_path**: Directory to monitor for file system events
- **api**: API server configuration (host, port, CORS settings)
- **security**: Authentication, rate limiting, and input validation settings
- **file_processing**: File processing parameters (checksum algorithm, chunk size, supported formats)
- **schemas**: Schema resolution and validation settings
- **version_control**: Git and DVC integration settings
- **monitor**: File system monitoring parameters
- **database**: Database connection settings (optional)
- **redis**: Redis cache configuration
- **frontend**: Frontend application settings

## Running the System

### Gateway-Based Architecture

The refactored system uses a gateway-based architecture where:

1. The gateway service manages user sessions and backend instance allocation
2. Users initiate sessions by providing a configuration file through the web interface
3. The gateway spawns dedicated backend instances for each session
4. All API requests are routed through the gateway to the appropriate backend instance

### Starting Services

#### Option 1: All Services (Local Development)

```bash
# Start gateway, backend, and frontend
make start

# Or using Docker Compose
docker-compose -f docker-compose.dev.yml up
```

#### Option 2: Gateway Only (Session-Based)

```bash
# Start gateway service
cd mdjourney-gateway
python main.py

# Access frontend at http://localhost:5173
# Frontend will prompt for configuration file on login
```

#### Option 3: Individual Components

```bash
# Start gateway
make start-gateway

# Start backend (standalone, for testing)
make start-backend

# Start frontend development server
make start-frontend
```

## Core Workflow

### Project Initialization

1. **Create Project Folder**: In the monitored directory, create a folder with the `p_` prefix (e.g., `p_MicrobiomeStudy2024`).

2. **Automatic Metadata Generation**: The file system monitor detects the new project folder and automatically creates `project_descriptive.json` in the `.metadata` subdirectory.

3. **Complete Project Metadata**: Access the web interface, select the project, and complete the project-level descriptive metadata fields (Principal Investigator, funding sources, project description, etc.).

### Dataset Creation

1. **Create Dataset Folder**: Within a project folder, create a dataset folder with the `d_` prefix (e.g., `d_PatientCohort_A`).

2. **Automatic Dataset Metadata**: The system generates `dataset_administrative.json` and `dataset_structural.json` files in the dataset's `.metadata` subdirectory.

3. **Complete Dataset Metadata**: Use the web interface to complete administrative metadata (license, access conditions, data steward contact) and structural metadata (dataset title, abstract, keywords).

### Data File Ingestion

1. **Add Data Files**: Place data files directly into dataset folders using standard file system operations.

2. **Automatic File Metadata Capture**: The file system monitor detects new files and automatically:
   - Calculates file checksums (SHA256)
   - Records file size, format, and MIME type
   - Captures file timestamps and permissions
   - Updates the dataset's structural metadata manifest

3. **No Manual Intervention Required**: File-level technical metadata is captured automatically without user action.

### Contextual Metadata Entry

1. **Create Experiment Template**: In the web interface, navigate to a dataset and select "Create Experiment Template."

2. **Select Contextual Schema**: Choose from available contextual schemas (e.g., genomics sequencing, microscopy imaging, anndata/mudata objects).

3. **Complete Contextual Details**: Fill in experiment-specific information including protocols, instrument settings, sample information, and quality control metrics.

4. **Save Contextual Metadata**: The system validates and saves the contextual metadata to `experiment_contextual.json`.

### Dataset Finalization

1. **Review Metadata Completeness**: Ensure all required metadata fields are completed and validated.

2. **Finalize Dataset**: Click the "Finalize Dataset" button in the web interface.

3. **Metadata Aggregation**: The system aggregates all metadata components (project descriptive, dataset administrative, dataset structural, experiment contextual, instrument technical) into a comprehensive FAIR-compliant metadata package.

4. **Version Control Integration**: If enabled, the system commits metadata changes to Git and tracks data files with DVC.

## Directory Structure

A typical project structure follows this organization:

```
/monitored/path/
└── p_ProjectName/                    # Project folder
    ├── .metadata/                    # Auto-managed metadata directory
    │   └── project_descriptive.json  # Project-level metadata
    └── d_DatasetName/                # Dataset folder
        ├── .metadata/                # Auto-managed metadata directory
        │   ├── dataset_administrative.json
        │   ├── dataset_structural.json
        │   └── experiment_contextual.json
        └── data_file_1.fastq.gz      # Data files
```

## API Endpoints

The backend API provides RESTful endpoints for metadata management. When accessed through the gateway, endpoints are prefixed with `/api/v1/`. Direct backend access uses `/v1/` prefix.

### Key Endpoints

- `GET /v1/health`: Health check endpoint
- `GET /v1/projects`: List all projects
- `GET /v1/projects/{project_id}/datasets`: List datasets in a project
- `GET /v1/datasets/{dataset_id}/metadata/{metadata_type}`: Retrieve specific metadata
- `PUT /v1/datasets/{dataset_id}/metadata/{metadata_type}`: Update metadata
- `POST /v1/datasets/{dataset_id}/contextual`: Create contextual metadata template
- `POST /v1/datasets/{dataset_id}/finalize`: Finalize a dataset
- `GET /v1/schemas/contextual`: List available contextual schemas
- `POST /v1/config/reload`: Reload configuration (admin)

## Development

### Development Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
cd mdjourney-backend
pip install -e ".[dev,test,api]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests
make test-integration

# Run with coverage
pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Type checking
make type-check
```

## Deployment

### Docker Production Deployment

```bash
# Build production images
make build-docker

# Start production services
make up

# View logs
make logs
```

### Environment Configuration

Copy `env.example` to `.env` and configure environment-specific settings:

```bash
cp env.example .env
# Edit .env with production values
```

Key environment variables:
- `MDJOURNEY_ENV`: Environment (development, staging, production)
- `MONITOR_PATH`: Directory to monitor
- `API_PORT`: Backend API port
- `GATEWAY_PORT`: Gateway service port
- `MDJOURNEY_API_KEY`: API authentication key
- `REDIS_HOST`, `REDIS_PORT`: Redis configuration

## Documentation

Comprehensive documentation is available in the `documentation/` directory:

- **System Architecture**: Detailed design and implementation (`documentation/explanation/system-architecture.md`)
- **Gateway Architecture**: Session-based backend management (`documentation/explanation/gateway-architecture.md`)
- **Configuration Management**: Configuration system documentation (`documentation/how-to-guides/configuration-management.md`)
- **API Reference**: Complete API endpoint documentation (`documentation/reference/api-endpoints.md`)
- **Codebase Glossary**: Component and concept reference (`documentation/reference/codebase_glossary.md`)

## Security Considerations

The system implements multiple security layers:

- **Input Validation**: All user inputs are validated against schemas and sanitized
- **Path Traversal Protection**: File system access is restricted to configured monitor paths
- **Rate Limiting**: API endpoints are protected by configurable rate limits
- **Authentication**: Optional API key-based authentication
- **Security Headers**: HTTP security headers are applied to all responses
- **Session Management**: Gateway-based session isolation prevents cross-user data access

## Performance Optimization

The system includes several performance optimizations:

- **Asynchronous Processing**: Background task processing for long-running operations
- **Caching**: Redis-based caching for schema resolution and metadata queries
- **Connection Pooling**: Database connection pooling for efficient resource utilization
- **File Processing**: Concurrent file processing with thread pools
- **Frontend Optimization**: Code splitting, lazy loading, and efficient state management

## Version Control Integration

MDJourney integrates with Git and DVC for metadata and data versioning:

- **Git**: Automatic commits for metadata file changes
- **DVC**: Data file tracking and versioning
- **Audit Trails**: Comprehensive change tracking through version control history

## Contributing

Contributions are welcome. Please see `CONTRIBUTING.md` for development guidelines, coding standards, and contribution workflow.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support and Contact

For issues, questions, or contributions, please use the project's issue tracker or contact the maintainers.

## Acknowledgments

MDJourney is developed to support FAIR data principles in scientific research, facilitating improved data discoverability, accessibility, interoperability, and reusability.