# Docker Setup and Usage

This document describes how to use Docker to run the FAIR Metadata Automation system.

## Overview

The system consists of four main services:
- **API**: FastAPI backend server
- **Frontend**: React frontend application
- **Monitor**: File system monitoring service
- **Redis**: Cache and session storage

## Ports

- Frontend (production): 8080
- Frontend (development): 5173
- API: 8000
- Redis: 6379

## Quick Start

### Production Environment

1. **Build and start all services:**
   ```bash
   make build-docker
   make up
   ```

2. **Access the application:**
   - Frontend: http://localhost:8080
   - API: http://localhost:8000
   - API Health: http://localhost:8000/api/v1/health

3. **Stop all services:**
   ```bash
   make down
   ```

### Development Environment

1. **Build and start development services:**
   ```bash
   make build-dev
   make up-dev
   ```

2. **Access the application:**
   - Frontend: http://localhost:5173 (with hot reload)
   - API: http://localhost:8000
   - API Health: http://localhost:8000/api/v1/health

3. **Stop development services:**
   ```bash
   make down
   ```

## Docker Compose Files

### Production (`docker-compose.yml`)
- Optimized for production deployment
- Frontend served via nginx
- Minimal volume mounts
- Health checks enabled

### Development (`docker-compose.dev.yml`)
- Hot reloading enabled
- Volume mounts for live code changes
- Development tools included
- Debug logging enabled

## Service Details

### API Service
- **Image**: Custom Python 3.11 image
- **Port**: 8000
- **Health Check**: HTTP GET /api/v1/health
- **Dependencies**: Redis
- **Volumes**:
  - `./monitor:/app/monitor`
  - `./schemas:/app/schemas`

### Frontend Service
- **Production**: nginx serving built React app
- **Development**: Vite dev server with hot reload
- **Port**: 8080 (production) / 5173 (development)
- **Health Check**: HTTP GET /
- **Dependencies**: API service

### Monitor Service
- **Image**: Custom Python 3.11 image
- **Health Check**: Process check for run_monitor.py
- **Dependencies**: API service
- **Volumes**:
  - `./monitor:/app/monitor`
  - `./schemas:/app/schemas`

### Redis Service
- **Image**: redis:alpine
- **Port**: 6379
- **Health Check**: redis-cli ping
- **Volumes**: redis_data

## Makefile Commands

### Build Commands
```bash
make build-docker   # Build production Docker images
make build-dev      # Build development Docker images
```

### Runtime Commands
```bash
make up             # Start production services
make up-dev         # Start development services
make down           # Stop all services
make restart        # Restart production services
make restart-dev    # Restart development services
```

### GUI Only (for decoupled architecture)
```bash
# Start just the frontend GUI in Docker
make up-frontend
```

### Monitoring Commands
```bash
make logs           # Show production logs
make logs-dev       # Show development logs
make ps             # Show running containers
make health         # Check service health
```

### Development Commands
```bash
make shell-api      # Shell into API container
make shell-frontend # Shell into frontend container
make shell-monitor  # Shell into monitor container
```

### Maintenance Commands
```bash
make clean-docker   # Remove all containers and images
make test           # Run tests
make lint           # Run linting
make format         # Format code
```

## Environment Variables

### API Service
- `MONITOR_PATH`: Path to monitor directory (default: /app/monitor)
- `LOG_LEVEL`: Logging level (INFO/DEBUG)
- `PYTHONPATH`: Python path (default: /app)

### Frontend Service
- `VITE_API_BASE_URL`: API base URL (default: http://localhost:8000)

### Monitor Service
- `MONITOR_PATH`: Path to monitor directory (default: /app/monitor)
- `LOG_LEVEL`: Logging level (INFO/DEBUG)
- `PYTHONPATH`: Python path (default: /app)

## Volume Mounts

### Production
- `./monitor:/app/monitor` - Monitor directory for file watching
- `./schemas:/app/schemas` - JSON schema definitions
- `redis_data:/data` - Redis data persistence

### Development
- All production volumes plus:
- `./app:/app/app` - Application code (live reload)
- `./api:/app/api` - API code (live reload)
- `./scripts:/app/scripts` - Scripts (live reload)
- `./frontend:/app` - Frontend code (hot reload)
- `/app/node_modules` - Node modules (excluded from hot reload)

## Health Checks

All services include health checks that monitor:
- **API**: HTTP endpoint availability
- **Frontend**: Web server availability
- **Monitor**: Process status
- **Redis**: Database connectivity

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check what's using the ports
   lsof -i :8000
   lsof -i :80
   lsof -i :5173
   ```

2. **Permission issues:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER monitor/
   sudo chown -R $USER:$USER schemas/
   ```

3. **Container won't start:**
   ```bash
   # Check logs
   make logs
   # Or for specific service
   docker-compose logs api
   ```

4. **Build failures:**
   ```bash
   # Clean and rebuild
   make clean-docker
   make build-docker
   ```

### Debug Mode

For debugging, you can run services in debug mode:
```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Start with debug
make up-dev
```

### Accessing Containers

```bash
# Shell into running containers
make shell-api
make shell-frontend
make shell-monitor

# Execute commands in containers
docker-compose exec api python -c "print('Hello from API')"
docker-compose exec frontend npm run build
```

## Production Deployment

For production deployment:

1. **Set environment variables:**
   ```bash
   export LOG_LEVEL=INFO
   export MONITOR_PATH=/data/monitor
   ```

2. **Build and start:**
   ```bash
   make build-docker
   make up
   ```

3. **Monitor health:**
   ```bash
   make health
   ```

4. **View logs:**
   ```bash
   make logs
   ```

## Security Considerations

- All containers run as non-root users
- Security headers are configured in nginx
- Health checks prevent zombie containers
- Volume mounts are restricted to necessary directories
- Environment variables are used for configuration

## Performance Optimization

- Multi-stage builds for smaller images
- Layer caching for faster builds
- Gzip compression enabled
- Static asset caching configured
- Redis for session storage and caching

## Mounting a specific host directory for the monitor

You can point the monitor to watch any host directory by overriding the volume that maps to `/app/monitor` in the container. The cleanest way is to create a `docker-compose.override.yml` alongside the existing compose file.

### Production override
Create `docker-compose.override.yml` with:
```yaml
services:
  monitor:
    volumes:
      - /absolute/path/to/your/data:/app/monitor
  api:
    volumes:
      - /absolute/path/to/your/data:/app/monitor
```
Then run:
```bash
docker-compose up -d
```
The override will merge with `docker-compose.yml`, replacing the default bind mount.

### Development override
For development, target the dev compose file with an override file, e.g. `docker-compose.dev.override.yml`:
```yaml
services:
  monitor:
    volumes:
      - /absolute/path/to/your/data:/app/monitor
  api:
    volumes:
      - /absolute/path/to/your/data:/app/monitor
```
Run both files together:
```bash
docker-compose -f docker-compose.dev.yml -f docker-compose.dev.override.yml up -d
```

### Notes
- Ensure the path on the host is absolute to avoid ambiguity.
- The `MONITOR_PATH` inside the containers is `/app/monitor` by default; do not change it unless you also update the environment variable accordingly.
- On macOS and Windows, make sure your virtualization (Docker Desktop) is granted access to the host path.
- Permissions: the containers run as a non-root user; ensure the mounted directory grants read (and when needed, write) permissions for scanning.