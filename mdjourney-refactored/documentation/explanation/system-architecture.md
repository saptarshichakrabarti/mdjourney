## FAIR-Compliant Research Data Metadata Automation System: Architecture & Implementation Details

### 1. Introduction

This document outlines the architectural details for implementing a system designed to automate the capture and management of FAIR-compliant metadata for research data. The primary goal is to minimize the burden on researchers while ensuring high-quality, discoverable, and reusable datasets.

### 2. Core Principles and Goals

*   **FAIR Principles:** Ensure metadata supports Findability, Accessibility, Interoperability, and Reusability.
*   **Automation:** Maximize automated metadata capture to reduce manual effort.
*   **User Experience (UX):** Provide intuitive interfaces for necessary manual input.
*   **Data Integrity:** Enforce consistency and validity of metadata.
*   **Provenance:** Track the origin and changes of data and metadata.
*   **Scalability:** Design for growth, anticipating large volumes of data and metadata.
*   **Modularity:** Structure the system in logical, separable components.

### 3. Metadata Schema Overview

The system manages metadata across six distinct categories, each with its own JSON schema, stored as `.json` files alongside the data. The system implements a **Schema Resolution Principle** that prioritizes local overrides over packaged defaults.

#### 3.1 Schema Resolution Principle

When the system needs a schema (e.g., to validate metadata), it follows a clear order of precedence:

1. **Local Override First**: Check if a `.template_schemas` directory exists within the current `MONITOR_PATH` (the specific data directory being managed). If it contains the required schema (e.g., `project_descriptive.json`), use this local version.

2. **Packaged Default Second**: If no local override is found, fall back to loading the default schema that was packaged with the application.

This allows for:
- **Customization**: Local modifications to schemas for specific projects or institutions
- **Version Control**: Local schemas can be version-controlled with the data
- **Backward Compatibility**: Always falls back to working defaults if local schemas are missing

#### 3.2 Metadata Categories

*   **Descriptive Metadata (Project Level):** High-level project context. Reusable for all datasets originating from this project. (e.g., `project_descriptive.json`)
*   **Administrative Metadata (Dataset Management Level):** Governs the dataset's lifecycle, access, rights, and compliance. (e.g., `dataset_administrative.json`)
*   **Structural Metadata (Dataset & File Level):** Uniquely identifies the dataset, describes its scope, constituent files, format, organization, and variables. (e.g., `dataset_structural.json`)
*   **Technical Metadata (Instrument Specification Level):** Static, reusable specifications for instruments. (e.g., `instrument_technical.json`)
*   **Contextual Metadata (Experiment Run Level):** Dynamic details of the specific experimental run(s) generating the data. (e.g., `experiment_contextual.json`)
*   **File Technical Metadata (NEW):** Specific technical properties of the digital file object itself (e.g., file type, encoding, dimensions, checksums). Auto-generated. (Integrated within `dataset_structural.json` for file entries.)

### 4. Gateway-Based Architecture

The refactored MDJourney system employs a gateway-based architecture that enables session-based backend instance management. This architecture provides enhanced flexibility for deployment scenarios ranging from local development to distributed high-performance computing environments.

#### 4.1 Gateway Service

The gateway service (`mdjourney-gateway/`) serves as the central entry point for all client requests. It manages user sessions, allocates backend instances, and routes requests to appropriate backend processes.

**Key Responsibilities:**
- Session initialization and management
- Backend process lifecycle management
- Request routing and proxying
- Configuration file handling
- Session state maintenance

**Technology Stack:**
- FastAPI for HTTP request handling
- Session middleware for state management
- httpx for asynchronous HTTP client operations
- Temporary file management for configuration storage

#### 4.2 Backend Service Architecture

Each backend instance operates as an independent FastAPI application with isolated configuration and state. Backend instances are spawned on-demand when user sessions are initiated.

**Instance Characteristics:**
- Isolated process space for complete session separation
- Per-session configuration loading
- Independent port allocation from configurable range
- Self-contained application state

**Technology Stack:**
- FastAPI for REST API implementation
- Pydantic for data validation
- ConfigManager for configuration handling
- SchemaManager for dynamic schema resolution

#### 4.3 Frontend Application

The web frontend (`mdjourney-webapp/`) provides the user interface for metadata management. It communicates with backend instances through the gateway service.

**Key Features:**
- Configuration file selection and upload
- Session initialization
- Metadata entry and editing interfaces
- Schema-driven form generation
- Real-time validation feedback

**Technology Stack:**
- React 18 with TypeScript
- Material-UI for component library
- TanStack Query for data fetching
- Zustand for state management
- js-yaml for configuration parsing

### 5. System Components & Technology Stack

This section details the various components of the system and the tools/technologies used for their implementation.

*   **File System Structure:**
    *   **Description:** A hierarchical folder structure where `p_ProjectName` indicates a Project Folder (enforced via naming convention), and other folders within (e.g., `dataset_RNASeq_rep1`) indicate Dataset Folders.
    *   **Tools:** Python's built-in `os` and `shutil` modules for directory and file operations.
*   **Triggers/Automation Engine:**
    *   **Description:** Automated scripts or services that respond to file system events (folder/file creation, modification) to initiate metadata processes.
    *   **Tools:**
        *   **Python-based (Development/Prototyping):** `watchdog` for real-time file system event monitoring, `APScheduler` for scheduled tasks.
        *   **OS-level (Production):** Operating System Cron Jobs (Linux/macOS) / Task Scheduler (Windows) for scheduled script execution, Systemd Services (Linux) for robust background services.
        *   **Cloud-native (Scalable):** AWS S3 Event Notifications / Azure Blob Storage Event Grid / Google Cloud Storage Event Notifications triggering serverless Python functions (AWS Lambda, Azure Functions, Google Cloud Functions).
*   **Metadata Files (JSON) & Schema Validation:**
    *   **Description:** The primary storage format for all metadata, adhering to predefined JSON schemas.
    *   **Tools:**
        *   Python's built-in `json` module for reading/writing JSON files.
        *   `jsonschema` (Python library) for validating JSON metadata against defined schemas.
        *   **SchemaManager**: Custom Python module that implements the Schema Resolution Principle, providing caching and local override support.
*   **User Interface (UI):**
    *   **Description:** A web-based or desktop application for researchers to input, review, and verify manual metadata. An initial version is already built, with plans for modular revamp.
    *   **Tools (Python-based examples):**
        *   **Web UI:** `Flask` or `Django` (Python web frameworks), `Streamlit` or `Dash` (Python dashboarding libraries for rapid prototyping).
        *   **Desktop UI:** `PyQt` or `Tkinter` (Python GUI libraries).
*   **`dirmeta` Library:**
    *   **Description:** A Python library used to automatically scan data files and generate file-level technical metadata (checksums, file sizes, format details, etc.). Confirmed as compliant with the defined schemas.
    *   **Tools:** `dirmeta` (Python library), integrated directly into Python scripts.
*   **Lab Information Management System (LIMS)/Electronic Lab Notebook (ELN):**
    *   **Description:** External systems providing source-of-truth data for samples, protocols, and experiments. LIMS is currently being implemented; direct integration will be a future enhancement.
    *   **Tools:**
        *   **Database Connectors/ORMs (Python):** `psycopg2`, `mysql-connector-python`, `pyodbc` for direct database connections; `SQLAlchemy` as an ORM.
        *   **HTTP Client (Python):** `requests` for interacting with LIMS/ELN REST APIs (if available).
*   **Version Control Systems (Git/DVC):**
    *   **Description:** Used to manage versions of both data (via DVC) and metadata files (via Git), providing inherent audit trails.
    *   **Tools:**
        *   **Command-line execution (Python):** Python's `subprocess` module to call Git and DVC commands.
        *   **Python Git library (Alternative):** `GitPython` for a more programmatic interface to Git.
*   **Metadata Catalog/Database (Future V2):**
    *   **Description:** A centralized database for efficient querying, aggregation, and management of metadata across all projects and datasets. Planned for Version 2.
    *   **Tools:**
        *   **SQL Databases:** PostgreSQL (with JSONB support highly recommended), MySQL.
        *   **NoSQL Databases:** MongoDB.
        *   **Graph Databases:** Neo4j (via `py2neo`), RDF stores (via `rdflib`).
        *   **Python Integration:** Python database drivers/ORMs (e.g., `SQLAlchemy`, `psycopg2`, `pymongo`).

### 5. Workflow Details

The system operates in a series of triggers and user actions, incrementally building and curating metadata for each data object. All system actions will adhere to the defined JSON schemas and include automated audit field population.

**Step 1: Project Initialization**
*   **User Action:** Researcher creates a new **Project Folder** (e.g., `/data/p_MyResearchProject`).
*   **System Action (Trigger 0 - Project Init):**
    *   Detects `p_` prefix in folder name.
    *   Generates a unique `Project Identifier` (e.g., UUID).
    *   Creates a `project_descriptive.json` template within the Project Folder.
*   **User Action:** Researcher fills out required project-level fields (Project Title, PI, Funding, etc.) via the UI, which updates `project_descriptive.json`. This file is validated against `project_descriptive_schema.json`.

**Step 2: Dataset Creation**
*   **User Action:** Researcher creates a **Dataset Folder** within a Project Folder (e.g., `/data/p_MyResearchProject/dataset_RNASeq_rep1`).
*   **System Action (Trigger 1 - Dataset Init):**
    *   Generates a unique `Dataset Identifier` (e.g., UUID).
    *   Creates `dataset_administrative.json` and `dataset_structural.json` templates within the Dataset Folder.
    *   Pre-populates `Associated Project Identifier` in both, linking back to the parent Project.
    *   `dataset_structural.json` is initialized with an empty `File Description(s)` array.
*   **User Action:** Researcher fills out required dataset-level administrative fields (Dataset Title, Abstract, Data Steward, License, Access Level, etc.) via the UI, which updates `dataset_administrative.json`. This file is validated against `dataset_administrative_schema.json`.

**Step 3: Data File Ingestion (V0 to V1)**
*   **User Action:** Researcher adds raw data file(s) to the Dataset Folder (e.g., `sample_A_read1.fastq.gz`). (This is implicitly "Version 0" of the data object).
*   **System Action (Trigger 2 - File Add):**
    *   Invokes `dirmeta` (or a similar tool) to scan the new file(s).
    *   `dirmeta` automatically generates file-specific technical metadata (e.g., `Checksum/Hash` (SHA256), `File Size(s)`, `File Format`, `MIME Type`, `Encoding`, `Dimensions`, `Number of Records/Rows`, timestamps, permissions).
    *   The `dataset_structural.json` in the parent Dataset Folder is **updated dynamically** by adding entries to its `File Description(s)` array, incorporating the details provided by `dirmeta`.
    *   The updated `dataset_structural.json` is re-validated against `dataset_structural_schema.json`.
*   **Outcome (Version 1):** The data file is now associated with its initial, automatically-captured file-level technical and structural metadata. This state represents "Version 1" of the data object, reflecting its raw, described form.

**Step 4: Contextual Metadata Capture (Leads to V2)**
*   **User Action:** For specific experimental runs (initially focusing on computational workflows), the researcher (via the UI) initiates the creation of an `experiment_contextual.json` file.
*   **System Action (Trigger 3 - Context Init):**
    *   Creates an `experiment_contextual.json` template.
    *   Pre-populates fields where possible (e.g., `Experiment Identifier / Run ID`, `Dataset Identifier Link`). `Instrument Used (Link)` can be selected from a pre-defined list if `instrument_technical.json` exists.
*   **User Action:** Researcher manually fills out *all* experiment-specific details via the UI. This includes: `Experiment Date(s)`, `Experimenter(s)`, `Protocol Reference(s)`, `Unique Sample/Batch Identifier(s)` (manual entry/placeholders for now), `Sample Source & Description`, `Sample Treatment(s)/Condition(s)`, `Sample Preparation Details` (manual entry for now), `Instrument Settings/Run Parameters`, `Software Used (Acquisition/Analysis)`, `Software Parameters/Script Used`, `Reagent/Kit Details`, `Quality Control (QC) Metrics`, `QC Assessment`, and `Experimenter Notes/Observations`. Saves changes.
*   **System Action (Trigger 4 - Context Complete):**
    *   `experiment_contextual.json` is validated against `experiment_contextual_schema.json`.
    *   This action signals completion of the detailed metadata for the associated data object(s).

**Step 5: Finalizing Data Object Version (V2 Creation)**
*   **System Action (Trigger 5 - V2 Finalize):**
    *   Upon completion and validation of the `experiment_contextual.json` for a specific data object (or set of objects from a run).
    *   A "Complete Metadata File" is generated. This file aggregates and links all relevant metadata: Project Descriptive, Dataset Administrative, Dataset Structural (including File Technical Metadata), Instrument Technical, and Contextual metadata for that specific data object/run.
    *   This "Complete Metadata File" (e.g., `data_object_X_v2_metadata.json` or an updated entry in a central catalog) now represents "Version 2" of the data object – its fully curated, FAIR-compliant state.
    *   The `dataset_structural.json` (acting as the manifest) in the parent folder is updated with a reference to this V2 metadata or marked as 'complete' for that file entry.

### 6. Key Design Decisions & Recommendations

*   **Identifier Management:** Implement automated internal GUID/UUID generation for `Project Identifier`, `Dataset Identifier`, `Experiment Identifier / Run ID`. Integrate with external services like DataCite for DOIs when data is published. Ensure all IDs are consistently referenced.
*   **JSON Schema and Validation:** Rigorously define and enforce JSON Schemas for all six metadata categories using `jsonschema`. Implement validation at every metadata write operation (UI submissions, trigger updates).
*   **User Interface (UI) for Manual Input:** Leverage the existing UI, revamping it for modularity and seamless integration with distinct metadata sections. The UI should abstract JSON details, pre-populate fields, and guide users with validation feedback.
*   **Integration Strategy:**
    *   **LIMS/ELN:** **(Future Enhancement within Phase 5):** Develop robust backend linkages (via database connectors like `SQLAlchemy` or API clients like `requests`) with your implemented LIMS to automatically pull sample, protocol, and experiment-related contextual metadata, reducing the need for manual input for these fields. Focus on a shared vocabulary.
    *   **Instrument Software:** Explore programmatic extraction of `Instrument Settings/Run Parameters` and `Software Used (Acquisition)` directly from raw instrument output files where possible.
    *   **Version Control (Git/DVC):** Utilize DVC for data versioning and Git for versioning of all JSON metadata files themselves. Automate commit operations for metadata changes using Python's `subprocess` module or `GitPython`.
*   **Data Provenance and Audit Trails:** Augment all JSON schemas with explicit audit fields (`created_by`, `created_date`, `last_modified_by`, `last_modified_date`). These will be automatically populated by the system or UI upon creation/modification, complementing DVC/Git history.

---

### 7. Development Roadmap

### Guiding Principles:
*   **Layered Development:** Build from core dependencies outwards.
*   **Test-Driven:** Each phase defines clear testing goals to ensure functionality before proceeding.
*   **Minimum Viable Product (MVP) Focus:** Deliver value incrementally.
*   **Python-Centric:** Leverage Python for core logic, integrating other tools as needed.

---

### Phase 0: Foundations & Setup (Pre-Development)

**Objective:** Prepare the development environment and define static assets.

*   **Key Features:**
    *   Define all six JSON metadata schemas (Project Descriptive, Administrative, Structural, Instrument Technical, Contextual, File Technical). Ensure consistency and validation rules.
    *   Establish project folder structure in your version control system (Git).
    *   Initial setup of Git repository for metadata and DVC for data tracking.
*   **Core Logic / Priority:** Essential prerequisite. Without schemas, development lacks a target.
*   **Dependencies:** None.
*   **Expected Output:**
    *   A set of `.json` schema files ready for validation.
    *   An empty, version-controlled project directory.
*   **Testing Focus:** Schemas are well-formed JSON and logically sound.
*   **Tools & Technologies:** JSON schema tools/documentation, Git.

---

### Phase 1: Core Metadata File Generation & Validation

**Objective:** Implement the basic automatic creation of metadata files and validate their structure based on folder events. This establishes the system's foundational responsiveness.

*   **Key Features:**
    *   **Folder Type Detection:** Logic to differentiate "Project Folders" (e.g., `p_prefix`) from "Dataset Folders."
    *   **Trigger 0 (Project Init):**
        *   On creation of a Project Folder: Automatically generate a unique `Project Identifier`.
        *   Create `project_descriptive.json` template within the Project Folder's `.metadata` subdirectory.
    *   **Trigger 1 (Dataset Init):**
        *   On creation of a Dataset Folder (within a Project Folder): Automatically generate a unique `Dataset Identifier`.
        *   Create `dataset_administrative.json` and `dataset_structural.json` templates within the Dataset Folder's `.metadata` subdirectory.
        *   Pre-populate `Associated Project Identifier` in both.
        *   Initialize `dataset_structural.json` with an *empty* `File Description(s)` array.
    *   **JSON Schema Validation:** Implement code to load and validate all generated JSON files against their respective schemas.
    *   **Basic Folder Monitoring:** A simple script (polling or `watchdog` for development) to detect new folder creations.
*   **Core Logic / Priority:** This is the absolute core. It verifies the system's ability to react to events and produce correctly structured, valid metadata containers.
*   **Dependencies:** Defined JSON schemas (from Phase 0).
*   **Expected Output:**
    *   When `/data/p_MyProject` is created: `project_descriptive.json` is created (in `.metadata`), valid, and contains a unique ID.
    *   When `/data/p_MyProject/dataset_A` is created: `dataset_administrative.json` and `dataset_structural.json` are created (in `.metadata`), valid, contain unique IDs, and are linked to the parent project ID.
*   **Testing Focus:**
    *   Are the correct JSON files generated in the correct `.metadata` locations for each folder type?
    *   Do all generated JSON files pass schema validation?
    *   Are identifiers and cross-references correctly generated and populated?
*   **Tools & Technologies:** Python `os`, `json`, `jsonschema`, `watchdog` (for dev/testing triggers).

---

### Phase 2: Automated File Technical Metadata Capture (V1 Data Object)

**Objective:** Integrate `dirmeta` to automatically extract and record file-specific technical metadata, establishing the "Version 1" data object state.

*   **Key Features:**
    *   **Trigger 2 (File Add):**
        *   Detection of new data files added to a Dataset Folder.
        *   Execution of `dirmeta` on new files.
        *   Parsing of `dirmeta` output and mapping its data (e.g., `path`, `extension`, `size_bytes`, timestamps, checksums) to the `File Technical Metadata` schema (embedded within `dataset_structural.json`).
        *   Dynamic update of the `File Description(s)` array within the `dataset_structural.json` (in the `.metadata` subdirectory of the parent Dataset Folder), adding entries for new files.
        *   Re-validation of the updated `dataset_structural.json`.
*   **Core Logic / Priority:** Automates the most volume-heavy and granular metadata capture, significantly reducing manual effort and ensuring a consistent baseline for data integrity (via checksums).
*   **Dependencies:** Phase 1 complete and stable. `dirmeta` Python library installed.
*   **Expected Output:**
    *   `dataset_structural.json` is automatically updated with correct, validated entries for each new data file added, including paths, sizes, and technical attributes.
    *   Data files implicitly achieve "Version 1" status (raw file + auto-generated metadata).
*   **Testing Focus:**
    *   Are all new files detected by Trigger 2?
    *   Is `dirmeta` output correctly parsed and mapped to your schema?
    *   Is `dataset_structural.json` dynamically updated correctly for each new file?
    *   Does the updated `dataset_structural.json` always remain schema-valid?
    *   Are checksums accurately generated and recorded?
*   **Tools & Technologies:** Python `os`, `json`, `jsonschema`, `dirmeta`.

---

### Phase 3: User Interface for Manual Metadata Input (MVP UX)

**Objective:** Provide a functional UI for researchers to input the initial manual metadata fields and trigger validation, making the system truly usable.

*   **Key Features:**
    *   **UI Forms:** Create web-based or desktop forms for:
        *   `Project Descriptive` metadata (initial population and editing).
        *   `Dataset Administrative` metadata (initial population and editing).
        *   Initial `Contextual Metadata` creation (for a specific experiment run/data object).
    *   **Read/Write Functionality:** UI can read existing JSON files (from their `.metadata` directories) to populate forms and save user input back to the corresponding JSON files.
    *   **Live/Client-side Validation:** Implement basic validation in the UI to guide users and provide immediate feedback based on JSON schemas.
*   **Core Logic / Priority:** This makes the system interactive and allows researchers to provide the crucial context that automation cannot capture.
*   **Dependencies:** Phase 1 complete (metadata files exist). Existing UI components/framework.
*   **Expected Output:** Researchers can successfully input, edit, and save manual metadata through the UI, with basic validation confirming data correctness.
*   **Testing Focus:**
    *   Can users navigate forms and input data correctly?
    *   Are changes saved accurately to the respective JSON files (in `.metadata` directories)?
    *   Does validation correctly prevent invalid submissions and provide clear error messages?
    *   Does the UI accurately display existing data from JSON files?
*   **Tools & Technologies:** Your existing Python UI framework (e.g., Flask/Django for web, PyQt/Tkinter for desktop).

---

### Phase 4: Provenance & Version Control

**Objective:** Integrate Git for metadata versioning and DVC for data versioning, establishing an automated and auditable history of changes.

*   **Key Features:**
    *   **Automated Git Commits:** Implement scripts that, after any metadata JSON file is created or modified (by triggers or the UI), automatically stage and commit the changes to Git. Commits should have meaningful messages.
    *   **Automated DVC Tracking:** Implement scripts to automatically add/update `.dvc` files for data files in the Dataset Folders whenever a data file changes or new files are added.
    *   **Audit Fields:** Programmatically populate `created_by`, `created_date`, `last_modified_by`, `last_modified_date` fields in *all* metadata JSON schemas whenever a file is created or modified by the system/UI. This provides explicit provenance within the metadata itself.
*   **Core Logic / Priority:** Ensures reproducibility, data integrity, and accountability by providing an immutable history of both data and its descriptive metadata.
*   **Dependencies:** Phases 1, 2, and 3 (to generate and modify files). Git and DVC installed and configured in the environment (at the `MONITOR_PATH` root).
*   **Expected Output:**
    *   A well-maintained Git repository history reflecting all metadata changes.
    *   `.dvc` files appearing alongside data files, tracking their versions.
    *   All metadata JSONs consistently containing populated audit fields.
*   **Testing Focus:**
    *   Are Git commits triggered reliably on every metadata change?
    *   Are DVC commands executed correctly for all data files?
    *   Are the audit fields (user, timestamp) correctly populated for all metadata files?
    *   Can you use Git/DVC commands to inspect metadata/data history and restore previous versions?
*   **Tools & Technologies:** Python `subprocess` (to call Git/DVC commands), Git, DVC.

---

### Phase 5: Contextual Metadata Completion & V2 Data Object Finalization (Initial for Computational Workflows)

**Objective:** Enable researchers to input, complete, and verify experiment-specific (initially computational workflow-specific) contextual metadata, and generate the comprehensive "Complete Metadata File" representing the fully curated data object (Version 2). Direct LIMS integration is deferred.

*   **Key Features:**
    *   **Trigger 3 (Context Init):** This trigger is activated (e.g., when a researcher signals a new experiment run), creating an `experiment_contextual.json` template within the relevant dataset's `.metadata` subdirectory.
    *   **UI for Contextual Data Entry:** Your enhanced UI (from Phase 3) will provide a user-friendly interface specifically for `experiment_contextual.json`. This UI should:
        *   Present the template for `experiment_contextual.json`.
        *   Allow researchers to manually fill in *all* experiment-specific details, including: `Experiment Date(s)`, `Experimenter(s)`, `Protocol Reference(s)`, `Unique Sample/Batch Identifier(s)` (manual entry/placeholders for now), `Sample Source & Description`, `Sample Treatment(s)/Condition(s)`, `Sample Preparation Details` (manual entry for now), `Instrument Used (Link)` (manual entry/selection from pre-defined list if `instrument_technical.json` exists), `Instrument Settings/Run Parameters`, `Software Used (Acquisition/Analysis)`, `Software Parameters/Script Used`, `Reagent/Kit Details`, `Quality Control (QC) Metrics`, `QC Assessment`, and `Experimenter Notes/Observations`.
        *   Offer a clear action (e.g., a "Mark Complete" button) to signify that the contextual metadata for a specific run is finalized.
    *   **Trigger 5 (V2 Finalize - "Complete Metadata File" Generation):** This trigger is activated when the `experiment_contextual.json` is marked complete and passes validation. It will:
        *   Aggregate and link all relevant metadata pieces: `project_descriptive.json`, `dataset_administrative.json`, `dataset_structural.json` (including `File Technical Metadata`), `instrument_technical.json` (referenced), and the newly completed `experiment_contextual.json`.
        *   Generate a single, comprehensive "Complete Metadata File" (e.g., `data_object_X_v2_metadata.json`) for the data object(s) associated with that run. This file *is* the Version 2 representation.
        *   Update the `dataset_structural.json` (in `.metadata`) to reference this V2 metadata or mark the relevant file entries as 'complete'.
*   **Core Logic / Priority:** Completes the automation of complex metadata and enables the full FAIR compliance of the data object, making it ready for downstream use or publication.
*   **Dependencies:** Phase 3 (UI).
*   **Expected Output:**
    *   Researchers can efficiently complete the contextual metadata for computational workflows.
    *   A "Complete Metadata File" is generated for each V2 data object, comprehensive and schema-valid.
*   **Testing Focus:**
    *   Does the UI effectively support the contextual data entry and "completion" workflow?
    *   Is the "Complete Metadata File" generated correctly, encompassing all metadata types from their respective `.metadata` directories?
    *   Does the "Complete Metadata File" pass its own schema validation?
*   **Tools & Technologies:** Python (core logic), your existing UI framework, `jsonschema`.
*   **Future Enhancement (within Phase 5): LIMS Integration:** Once the LIMS is operational, build Python modules to query its backend (database or API) to automatically pre-populate `experiment_contextual.json` fields (e.g., sample IDs, sources, treatments) that are currently manually entered.

---

### 8. Future Considerations (V2 Roadmap)

These phases build upon the MVP established above and address scalability, robustness, and long-term data management.

### Phase 6: Scalability & Centralized Querying

**Objective:** Implement a centralized database to efficiently store, search, and aggregate all metadata.

*   **Key Features:**
    *   **Database Setup:** Deploy and configure a chosen database (e.g., PostgreSQL with JSONB, MongoDB).
    *   **Metadata Ingestion Service:** A service to read all existing JSON metadata files from disk (including those in `.metadata` directories) and ingest them into the database.
    *   **Real-time Synchronization:** Implement logic to ensure metadata changes (from triggers or UI) are not just written to JSON files, but also synchronized with the database in real-time.
    *   **Search/Query API:** Develop an API layer on top of the database to enable powerful, cross-project/dataset search and filtering of metadata.
*   **Dependencies:** All previous phases completed.
*   **Tools & Technologies:** Python database drivers/ORMs (e.g., `SQLAlchemy`, `psycopg2`, `pymongo`).

### Phase 7: Robustness & Operational Monitoring

**Objective:** Enhance system reliability, error handling, and provide operational visibility.

*   **Key Features:**
    *   **Comprehensive Logging:** Implement detailed logging across all system components and triggers.
    *   **Error Handling:** Implement robust error handling mechanisms within all scripts and UI, including retry logic for transient issues.
    *   **Alerting System:** Integrate with an alerting system (e.g., email, Slack, PagerDuty) to notify administrators of critical failures or validation errors.
    *   **Monitoring:** Implement metrics collection (e.g., number of files processed, processing time, errors) and integrate with a monitoring dashboard (e.g., Prometheus/Grafana).
    *   **Containerization:** Containerize all Python services (triggers, UI backend) using Docker for consistent deployment.
*   **Dependencies:** Phase 6 for potential logging to database.
*   **Tools & Technologies:** Python `logging` module, specific logging/monitoring libraries (e.g., `Loguru`, `Prometheus_client`), Docker, Systemd (for service management), cloud-specific monitoring tools.

### Phase 8: Data Retention & Archival Automation

**Objective:** Automate processes for long-term data preservation and facilitate submission to external repositories.

*   **Key Features:**
    *   **Policy Engine:** Develop logic to interpret the `Data Retention Schedule` field from `dataset_administrative.json` and trigger actions based on it.
    *   **Automated Archival Transfer:** Implement integrations to automatically push V2 data objects (and their "Complete Metadata Files") to designated long-term repositories or archival storage solutions.
    *   **Metadata Migration Utilities:** Develop tools to handle future metadata schema changes, ensuring forward and backward compatibility or providing migration scripts.
*   **Dependencies:** Phase 6 (centralized metadata for policy enforcement).
*   **Tools & Technologies:** Repository-specific APIs/SDKs, data transfer tools.

---