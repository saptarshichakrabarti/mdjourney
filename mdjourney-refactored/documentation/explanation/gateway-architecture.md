# Gateway-Based Architecture

This document provides a comprehensive explanation of the gateway-based architecture implemented in the refactored MDJourney system. It describes the design rationale, component interactions, session management, and deployment considerations.

## Introduction

The refactored MDJourney system employs a gateway-based architecture that enables session-based backend instance management. This architecture provides enhanced flexibility for deployment scenarios ranging from local development to distributed high-performance computing environments, while maintaining isolation between user sessions and configurations.

## Architectural Overview

### Design Principles

The gateway architecture is founded on several key principles:

1. **Session Isolation**: Each user session operates with an independent backend instance, ensuring complete isolation of data and configuration.

2. **Dynamic Backend Allocation**: Backend instances are created on-demand when sessions are initiated, allowing efficient resource utilization.

3. **Configuration Flexibility**: Each session can operate with a distinct configuration, enabling multiple users or use cases to coexist.

4. **Request Routing**: The gateway serves as a central routing point, directing requests to the appropriate backend instance based on session context.

5. **Scalability**: The architecture supports horizontal scaling by allowing multiple backend instances to run concurrently.

### Component Architecture

The system consists of three primary components:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                  (React Web Application)                    │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        │ HTTP Requests
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                      Gateway Service                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Session Management                                  │   │
│  │  - Session initialization                          │   │
│  │  - Backend instance allocation                      │   │
│  │  - Configuration management                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Request Routing                                    │   │
│  │  - Request proxying                                 │   │
│  │  - Session context resolution                       │   │
│  │  - Error handling                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└───────┬───────────────────────────────────┬─────────────────┘
        │                                   │
        │                                   │
┌───────▼──────────┐              ┌────────▼──────────────┐
│  Backend Instance│              │  Backend Instance      │
│  (Session A)     │              │  (Session B)           │
│  Port: 8001      │              │  Port: 8002           │
│  Config: A       │              │  Config: B             │
└──────────────────┘              └───────────────────────┘
```

## Gateway Service

### Responsibilities

The gateway service (`mdjourney-gateway/`) performs the following functions:

1. **Session Initialization**: Accepts configuration files from users and creates new sessions.

2. **Backend Process Management**: Spawns and manages backend process instances for each session.

3. **Request Proxying**: Routes incoming API requests to the appropriate backend instance based on session context.

4. **Session State Management**: Maintains session state including backend port assignments and configuration file paths.

5. **Health Monitoring**: Provides health check endpoints for monitoring gateway status.

### Session Lifecycle

#### Session Initialization

1. User accesses the web frontend and is prompted to select a configuration file.

2. Frontend parses the YAML configuration file and converts it to JSON format.

3. Frontend sends a POST request to `/api/session/start` with the configuration JSON.

4. Gateway receives the configuration and:
   - Validates the configuration structure
   - Allocates an available port for the backend instance
   - Creates a temporary configuration file (JSON format)
   - Spawns a new backend process with the configuration file path
   - Stores session information (backend port, process ID, config path) in session storage

5. Gateway returns a success response to the frontend.

#### Request Processing

1. Frontend sends API requests to the gateway at `/api/v1/{endpoint}`.

2. Gateway extracts session information from the request context.

3. Gateway resolves the backend port associated with the session.

4. Gateway forwards the request to the backend instance at `http://localhost:{backend_port}/v1/{endpoint}`.

5. Gateway receives the backend response and forwards it to the frontend.

6. Frontend processes the response and updates the user interface.

#### Session Termination

Sessions are terminated when:

- User explicitly logs out through the frontend
- Backend process terminates unexpectedly
- Session timeout expires (if configured)
- Gateway service is restarted (sessions are not persisted)

## Backend Service

### Instance Characteristics

Each backend instance operates as an independent FastAPI application with the following characteristics:

1. **Isolated Configuration**: Each instance loads configuration from a session-specific file provided at startup.

2. **Port Assignment**: Instances are assigned unique ports from a configurable range (default: 8001-8010).

3. **Process Isolation**: Instances run as separate processes, ensuring complete isolation of memory and file system access.

4. **Independent State**: Each instance maintains its own application state, including loaded configurations and cached schemas.

### Configuration Loading

Backend instances load configuration through the following process:

1. Gateway passes configuration file path as command-line argument: `--config-file /tmp/config_xyz.json`

2. Backend's `load_configuration()` function:
   - Initializes `ConfigManager` with the configuration file path
   - Loads configuration (supports both JSON and YAML)
   - Normalizes configuration keys (converts gateway-style camelCase to internal snake_case)
   - Substitutes environment variables
   - Validates configuration structure
   - Initializes global configuration state

3. Backend starts FastAPI application with the loaded configuration.

### API Endpoint Structure

Backend instances expose endpoints with the `/v1/` prefix:

- `GET /v1/health`: Health check endpoint
- `GET /v1/projects`: List projects
- `GET /v1/projects/{project_id}/datasets`: List datasets
- `GET /v1/datasets/{dataset_id}/metadata/{metadata_type}`: Retrieve metadata
- `PUT /v1/datasets/{dataset_id}/metadata/{metadata_type}`: Update metadata
- `POST /v1/datasets/{dataset_id}/contextual`: Create contextual template
- `POST /v1/datasets/{dataset_id}/finalize`: Finalize dataset

When accessed through the gateway, these endpoints are available at `/api/v1/{endpoint}`.

## Frontend Application

### Session Initialization Flow

The frontend (`mdjourney-webapp/`) implements the following session initialization flow:

1. **Login Page**: User is presented with a file input for selecting a configuration file.

2. **File Selection**: User selects a YAML configuration file (typically `sample-config.yaml`).

3. **File Parsing**: Frontend uses `js-yaml` library to parse the YAML file into a JavaScript object.

4. **Session Start**: Frontend sends POST request to `/api/session/start` with the parsed configuration.

5. **Authentication State**: Upon successful session creation, frontend updates authentication state and navigates to the main application.

6. **API Requests**: All subsequent API requests are sent to `/api/v1/{endpoint}`, which are routed through the gateway.

### Configuration File Format

The frontend expects configuration files in YAML format matching the structure defined in `fair_meta_config_template.yaml`. The configuration is converted to JSON before transmission to the gateway, ensuring compatibility with the backend's configuration loading system.

## Configuration Management

### Configuration File Structure

Configuration files follow a hierarchical structure defined by the template:

```yaml
monitor_path: "./data"
environment: "development"
api:
  host: "0.0.0.0"
  port: 8000
security:
  authentication:
    enabled: false
schemas:
  base_path: "packaged_schemas"
  custom_path: null
```

### Key Normalization

The system implements automatic key normalization to support both gateway-style (camelCase) and template-style (snake_case) formats:

- `watchDirectory` → `monitor_path`
- `templateDirectory` → `schemas.custom_path`
- `watchPatterns` → `monitor.ignore_patterns`

This normalization ensures backward compatibility while promoting the use of the standard template format.

### Environment Variable Substitution

Configuration values support environment variable substitution using the syntax `${VAR_NAME}` or `${VAR_NAME:-default}`:

```yaml
security:
  authentication:
    api_key: "${MDJOURNEY_API_KEY:-default-key}"
```

## Deployment Considerations

### Local Development

For local development, all components can run on the same machine:

```bash
# Start gateway
cd mdjourney-gateway
python main.py

# Start frontend (in separate terminal)
cd mdjourney-webapp
npm run dev
```

The gateway manages backend instances automatically when sessions are initiated.

### Containerized Deployment

Docker Compose configurations support both development and production deployments:

**Development** (`docker-compose.dev.yml`):
- Volume mounts for live code reloading
- Development logging levels
- Hot-reload enabled for frontend

**Production** (`docker-compose.yml`):
- Optimized builds
- Read-only file systems for security
- Health checks and restart policies
- Resource limits and scaling options

### Distributed Deployment

The gateway architecture supports distributed deployment scenarios:

1. **Gateway on Public Server**: Gateway service exposed to users
2. **Backend Instances on Compute Nodes**: Backend instances spawned on HPC compute nodes
3. **Frontend Served Separately**: Frontend can be served from CDN or separate web server

This architecture enables efficient resource utilization in HPC environments where compute nodes can be allocated dynamically.

## Security Considerations

### Session Isolation

Each backend instance operates with complete isolation:

- Separate process space prevents memory access between sessions
- Independent configuration prevents cross-session data access
- Port-based routing ensures request isolation

### Configuration Security

- Configuration files are stored in temporary locations with restricted permissions
- Sensitive configuration values should use environment variable substitution
- API keys and credentials should not be hardcoded in configuration files

### Network Security

- Gateway should be deployed behind appropriate firewall rules
- Backend instances should only accept connections from localhost
- HTTPS should be used in production deployments

## Performance Characteristics

### Resource Utilization

- Backend instances are created on-demand, reducing idle resource consumption
- Each instance operates independently, enabling parallel processing
- Gateway overhead is minimal, primarily consisting of request routing

### Scalability

The architecture supports horizontal scaling:

- Multiple gateway instances can be deployed behind a load balancer
- Backend instances can be distributed across multiple machines
- Session affinity ensures consistent routing

### Limitations

Current implementation limitations:

- Session state is stored in memory (not persistent across gateway restarts)
- Port allocation is limited to a fixed range
- Backend instance cleanup requires manual intervention in some scenarios

## Monitoring and Observability

### Health Checks

- Gateway provides `/api/health` endpoint
- Each backend instance provides `/v1/health` endpoint
- Docker health checks monitor service availability

### Logging

- Gateway logs session creation and request routing
- Backend instances log configuration loading and API requests
- Structured logging enables aggregation and analysis

### Metrics

Recommended metrics for monitoring:

- Number of active sessions
- Backend instance count
- Request latency through gateway
- Backend instance resource utilization
- Session creation and termination rates

## Future Enhancements

### Planned Improvements

1. **Persistent Session Storage**: Implement database-backed session storage for persistence across gateway restarts

2. **Enhanced Port Management**: Dynamic port allocation with broader range and conflict resolution

3. **Automatic Cleanup**: Implement automatic cleanup of terminated backend instances

4. **Session Timeout**: Configurable session timeout with automatic termination

5. **Multi-User Support**: Role-based access control and user authentication

6. **Load Balancing**: Intelligent backend instance allocation based on resource availability

7. **Monitoring Integration**: Enhanced metrics and observability integration

## Conclusion

The gateway-based architecture provides a flexible foundation for the MDJourney system, enabling efficient resource utilization, session isolation, and scalable deployment. The architecture supports diverse deployment scenarios while maintaining the core functionality of automated FAIR metadata management.

This design facilitates the system's use in both local development environments and distributed computing infrastructures, making it suitable for a wide range of research data management scenarios.
