# MDJourney - FAIR Metadata Automation System

Welcome to MDJourney, your automated companion for creating FAIR-compliant (Findable, Accessible, Interoperable, Reusable) research data.

MDJourney works by "watching" your data folders. Instead of forcing you to enter metadata into complex separate systems right away, it lets you work naturally in your file explorer. When you create folders or add data, MDJourney automatically generates the necessary metadata templates in the background, and the modern web interface makes it easy to provide the human-readable details when you are ready.

### Key Concepts
- **Automation First**: The system automatically captures technical details like file sizes, formats, and checksums so you don't have to.
- **Folder-Driven**: Your directory structure dictates the metadata structure.
- **The `.metadata` folder**: MDJourney creates hidden `.metadata` subfolders alongside your data to store its JSON records. **Do not delete or manually edit files in this folder.**

---

## Getting Started with MDJourney

This guide will walk you through setting up the system and using its core features.

### 1. Installation

First, clone the repository and run the automated installer. This handles all dependencies and creates an isolated environment for the backend.

**Prerequisites:**
- Python 3.8+ and Git
- **Docker**: Highly recommended for the easiest setup. If you use Docker, you **do not** need to install Node.js.
- **Node.js 18+**: *Optional.* Only needed if you run the frontend *without* Docker.
- **DVC**: *Optional,* for data versioning.

```bash
# Get the code
git clone https://github.com/saptarshichakrabarti/mdjourney.git
cd mdjourney

# Run the automated installer
make install
```

### 2. Configuration (Crucial First Step)

You must tell MDJourney which main folder it should "watch" for your research data.

```bash
# This creates the .fair_meta_config.yaml configuration file
make setup
```
This command will prompt you to enter the **absolute path** to your data directory. This is the most important setting. The system will now monitor this path for changes.

### 3. Choose Your Setup

MDJourney supports two primary operational modes.

#### Option A: Local Setup (All-in-One)
Best for running everything on your personal computer.

```bash
# Start all components (monitor, API, frontend) using Docker
make start
```
You can now access the **Web Interface at http://localhost:5173**.

#### Option B: Decoupled Setup (Remote Server/HPC)
**This is the recommended setup for HPC users.** The backend runs on the remote server where your data resides, and you use the web interface on your local machine.

**Step 1: On the Remote Server (e.g., HPC)**
1. Follow the **Installation** and **Configuration** steps above on the server.
2. Start the backend services ONLY:
   ```bash
   make start-backend
   ```
   The server is now monitoring your files.

**Step 2: On Your Local Machine**
1. Open a new terminal and create a secure **SSH tunnel** to the server.
   ```bash
   # General command format
   ssh -L 8000:localhost:8000 <username>@<server-host> -N
   ```
   *For detailed guidance, especially for multi-node HPCs, see the [Decoupled Architecture Guide](documentation/how-to-guides/decoupled-architecture.md).*

2. In another terminal on your local machine (inside the cloned project folder), start the frontend GUI ONLY:
   ```bash
   make up-frontend
   ```
You can now access the **Web Interface at http://localhost:8080** on your local machine, which is securely connected to your remote backend.

### 4. Core Workflow: From Data to Metadata

Whether running locally or remotely, the workflow is the same. MDJourney uses folder names to understand your project structure.

#### 1. Start a Project (`p_` prefix)
Create a folder in your monitored directory starting with `p_`.

- **Action:** In your file explorer, create a folder like `/path/to/data/p_MicrobiomeStudy2024`.
- **System Response:** MDJourney detects the `p_` prefix and automatically creates the initial project metadata file.
- **Your Task:** Open the web interface. You will see your new project. Click it to fill in high-level details (e.g., Principal Investigator, Grant Number).

#### 2. Create Datasets (`d_` prefix)
Inside a project folder, create dataset folders starting with `d_`.

- **Action:** Create a subfolder like `.../p_MicrobiomeStudy2024/d_PatientCohort_A`.
- **System Response:** The system generates administrative and structural metadata files for this new dataset.
- **Your Task:** In the web interface, select this dataset to set details like licenses and access rights.

#### 3. Add Data Files (Zero-Touch Automation)
Simply drag and drop your data files into a dataset folder.

- **Action:** Move `sequencing_run1.fastq.gz` into the `d_PatientCohort_A` folder.
- **System Response:** MDJourney detects the file, calculates its checksum and size, and automatically adds an entry to the dataset's manifest.
- **Your Task:** None. The file's technical metadata is now tracked automatically.

#### 4. Add Contextual Details
When you are ready to document experiment-specific details:

1. Navigate to your dataset in the web interface.
2. Click **"Create Experiment Template"**.
3. Fill in the form with details like protocols used, instrument settings, etc., and click **Save**.

#### 5. Finalize a Dataset
When a dataset is complete and fully described:

1. Ensure all required metadata fields in the UI are filled and valid (green).
2. Click the **"Finalize Dataset"** button in the right-hand panel.
3. **System Response:** MDJourney aggregates all related metadata into a single, comprehensive, FAIR-compliant JSON package.

### Folder Structure Summary
A well-organized project will look like this:
```
/ResearchData/ (Your monitored path)
└── p_MicrobiomeStudy2024/             <-- Project Folder
    ├── .metadata/                     <-- Auto-managed by MDJourney
    │   └── project_descriptive.json
    └── d_PatientCohort_A/             <-- Dataset Folder
        ├── .metadata/                 <-- Auto-managed by MDJourney
        │   ├── dataset_administrative.json
        │   └── dataset_structural.json
        └── sequencing_run1.fastq.gz   <-- Your data file
```

---

## Technical Reference & Developer Information

For developers and advanced users, the following sections provide detailed technical information about the system.

### Makefile Commands

```bash
# Start the complete system (monitor + API + frontend)
make start

# Start individual components
make start-api      # API server only
make start-monitor  # File system monitor only
make start-frontend # Frontend development server only (non-Docker)
make up-frontend    # Frontend GUI only (in Docker)
make start-backend  # API + monitor (for decoupled setup)

# Testing
make test           # Run all tests
make test-unit      # Unit tests only
make test-integration # Integration tests only

# Code quality
make lint           # Run linters
make format         # Format code
```

### Service URLs
When running locally, the services are available at:
- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Features
- **File Upload System**: Upload supporting files directly to datasets through the web interface.
- **Version Control Integration**: Optional Git and DVC integration for data and metadata versioning.
- **Dynamic Schema Resolution**: Supports local schema overrides on top of packaged defaults.
- **Schema-Driven Validation**: Ensures metadata quality and consistency.

### Architecture
- **Backend API** (`api/`): A FastAPI-based REST API.
- **Application Services** (`app/`): Core business logic.
- **Frontend** (`frontend/`): A React and TypeScript web interface.
- **File Monitor**: A service for real-time file system monitoring.
- **Schema Management**: Handles dynamic schema resolution and validation.

### Key Technologies
- **Backend**: FastAPI, Pydantic, SQLAlchemy, Redis, Celery
- **Frontend**: React 18, TypeScript, Material-UI, TanStack Query, Zustand, Vite
- **Infrastructure**: Docker, Nginx, Git/DVC

### Documentation
Comprehensive documentation is available in the `documentation/` directory, including:
- **System Architecture**: Detailed design and implementation.
- **How-to Guides**: For configuration, Docker, testing, and contributing.
- **Reference**: API Endpoints and a Codebase Glossary.

### API Reference
The system provides a comprehensive REST API. Key endpoints include:
- `GET /api/v1/projects`: List all projects.
- `GET /api/v1/projects/{project_id}/datasets`: List datasets in a project.
- `PUT /api/v1/datasets/{dataset_id}/metadata/{metadata_type}`: Update metadata.
- `POST /api/v1/datasets/{dataset_id}/finalize`: Finalize a dataset.
- `GET /api/v1/health`: Health check for the API.

### Deployment with Docker
- **Production**: `make build-docker` then `make up`
- **Development**: `make build-dev` then `make up-dev`

### Security & Performance
The system is optimized for performance and includes security features such as input validation, path traversal protection, rate limiting, and optional authentication. Performance is enhanced through asynchronous processing, a Redis-based caching layer, and frontend optimizations.

### Contributing
We welcome contributions! Please see our [Contributing Guide](documentation/how-to-guides/contributing.md) for details on the development setup, coding standards, and pull request process.

### License
This project is licensed under the MIT License - see the LICENSE file for details.
