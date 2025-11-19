.PHONY: help build build-docker build-dev up up-dev down logs clean clean-docker test lint format type-check package install-dev venv-create venv-activate venv-install venv-clean reqs sync start start-backend start-api start-monitor start-frontend start-gateway setup setup-dev health ps restart restart-dev shell-api shell-frontend shell-monitor pre-commit-install pre-commit-run frontend-install frontend-build frontend-dev frontend-preview frontend-lint frontend-clean up-backend up-frontend build-frontend-docker down-frontend logs-frontend build-all dev-all clean-all

# Default target
help:
	@echo "Backend Development Commands:"
	@echo "============================="
	@echo "  Virtual Environment:"
	@echo "    venv-create  - Create Python virtual environment"
	@echo "    venv-install - Install dependencies in virtual environment"
	@echo "    venv-clean   - Remove virtual environment"
	@echo "    install-all  - Create venv and install all dependencies"
	@echo "    install      - Install dependencies (creates venv automatically)"
	@echo "    reqs         - Compile requirements-api.txt and requirements-dev.txt from pyproject.toml"
	@echo "    reqs-base    - Compile requirements-base.txt from core dependencies"
	@echo "    reqs-dev     - Compile requirements-dev.txt from [dev, test, api] extras"
	@echo "    reqs-test    - Compile requirements-test.txt from [test] extras"
	@echo "    reqs-api     - Compile requirements-api.txt from [api] extras"
	@echo "    sync         - Sync virtual environment with pinned dependencies"
	@echo "    setup        - Initial setup and configuration [auto-venv]"
	@echo "    test         - Run tests [auto-venv]"
	@echo "    test-unit    - Run unit tests only [auto-venv]"
	@echo "    test-integration - Run integration tests only [auto-venv]"
	@echo "    lint         - Run linting [auto-venv]"
	@echo "    format       - Format code [auto-venv]"
	@echo "    type-check   - Type checking [auto-venv]"
	@echo "  Services:"
	@echo "    start        - Start all services (API + Monitor + Frontend) [auto-venv]"
	@echo "    start-backend - Start backend services only (API + Monitor) [auto-venv]"
	@echo "    start-api    - Start API server only [auto-venv]"
	@echo "    start-monitor - Start monitor only [auto-venv]"
	@echo "    start-frontend - Start frontend only"
	@echo "    start-gateway - Start gateway service"
	@echo "  Frontend:"
	@echo "    frontend-install - Install frontend dependencies"
	@echo "    frontend-build   - Build frontend for production"
	@echo "    frontend-dev     - Start frontend development server"
	@echo "    frontend-preview - Preview production build"
	@echo "    frontend-lint    - Run frontend linting"
	@echo "    frontend-clean   - Clean frontend build artifacts"
	@echo "  Combined:"
	@echo "    install-all  - Create venv and install all dependencies"
	@echo "    build-all    - Build both backend and frontend"
	@echo "    dev-all      - Start backend services and frontend dev server"
	@echo "    clean-all    - Clean both backend and frontend artifacts"
	@echo "  Packaging:"
	@echo "    build        - Build Python package"
	@echo "    clean        - Clean build/test/cache artifacts"
	@echo "    package      - Build Python package"
	@echo "    package-clean - Clean build artifacts"
	@echo "    package-check - Check package integrity"
	@echo "  Git Hooks:"
	@echo "    pre-commit-install - Install pre-commit hooks (black, isort, flake8, pytest)"
	@echo "    pre-commit-run     - Run all pre-commit hooks on all files"
	@echo "  Docker:"
	@echo "    build-docker - Build production Docker images"
	@echo "    build-dev    - Build development Docker images"
	@echo "    up           - Start production services"
	@echo "    up-dev       - Start development services"
	@echo "    up-backend   - Start backend services only (for server deployment)"
	@echo "    up-frontend  - Start frontend service only"
	@echo "    down         - Stop all services"
	@echo "    logs         - Show logs from all services"
	@echo "    clean-docker - Remove all containers and images"

# Virtual Environment Management
VENV_DIR = .venv
PYTHON = python3
PIP = pip

# Check if virtual environment exists
venv-exists:
	@test -d $(VENV_DIR) || (echo "Virtual environment not found. Run 'make venv-create' first." && exit 1)

# Create virtual environment (idempotent)
venv-create:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment in $(VENV_DIR)..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "Virtual environment created successfully!"; \
	else \
		echo "Virtual environment already exists in $(VENV_DIR)"; \
	fi
	@echo "To activate manually: source $(VENV_DIR)/bin/activate"

# Install dependencies in virtual environment (idempotent)
venv-install: venv-create
	@echo "Installing dependencies in virtual environment..."
	@$(VENV_DIR)/bin/python -m pip install --upgrade pip setuptools wheel || \
		($(VENV_DIR)/bin/python -m ensurepip --upgrade && \
		$(VENV_DIR)/bin/python -m pip install --upgrade pip setuptools wheel)
	@$(VENV_DIR)/bin/python -m pip install -e ".[dev,test,api]"
	@echo "Dependencies installed successfully!"

# Clean virtual environment
venv-clean:
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)
	@echo "Virtual environment removed!"

# Convenience target: create venv and install everything
install-all: venv-create venv-install
	@echo "Virtual environment created and dependencies installed!"
	@echo "Run 'make start' to start the services."

# Development setup
install-dev:
	@if ! pip show mdjourney > /dev/null 2>&1; then \
		echo "Installing dependencies..."; \
		cd mdjourney-backend && pip install -e ".[dev,test,api]"; \
		echo "Dependencies installed successfully!"; \
	else \
		echo "Dependencies already installed (skipping reinstall)"; \
	fi

# Default install: create venv if needed, then install
install: venv-create venv-install
	@if [ -f mdjourney-backend/requirements-api.txt ] && [ -f mdjourney-backend/requirements-dev.txt ]; then \
		echo "Pinned requirements files found. Running sync..."; \
		$(VENV_BIN)/pip-sync mdjourney-backend/requirements-api.txt mdjourney-backend/requirements-dev.txt; \
	else \
		echo "No pinned requirements files found. Using pyproject.toml."; \
	fi
	@echo "Dependencies installed successfully!"
	@echo "Virtual environment is ready. Use 'make start' to run services."

# Requirements management using pip-tools
VENV_BIN=./.venv/bin

# Compile all into a single constraints-style file combining base and extras
reqs:
	@echo "Compiling requirements..."
	$(VENV_BIN)/pip-compile --resolver=backtracking --generate-hashes -o mdjourney-backend/requirements-api.txt pyproject.toml
	$(VENV_BIN)/pip-compile --resolver=backtracking --extra dev --extra test --extra api --generate-hashes -o mdjourney-backend/requirements-dev.txt pyproject.toml
	@echo "Done."

# Base requirements (no extras)
reqs-base:
	@echo "Compiling base requirements..."
	$(VENV_BIN)/pip-compile --resolver=backtracking --generate-hashes -o mdjourney-backend/requirements-base.txt pyproject.toml
	@echo "Done."

# Dev requirements (includes dev, test, and api extras)
reqs-dev:
	@echo "Compiling dev requirements..."
	$(VENV_BIN)/pip-compile --resolver=backtracking --extra dev --extra test --extra api --generate-hashes -o mdjourney-backend/requirements-dev.txt pyproject.toml
	@echo "Done."

# Test requirements
reqs-test:
	@echo "Compiling test requirements..."
	$(VENV_BIN)/pip-compile --resolver=backtracking --extra test --generate-hashes -o mdjourney-backend/requirements-test.txt pyproject.toml
	@echo "Done."

# API requirements
reqs-api:
	@echo "Compiling API requirements..."
	$(VENV_BIN)/pip-compile --resolver=backtracking --extra api --generate-hashes -o mdjourney-backend/requirements-api.txt pyproject.toml
	@echo "Done."

# Sync virtual environment with pinned dependencies
sync: venv-exists
	@echo "Syncing virtual environment with pinned dependencies..."
	$(VENV_BIN)/pip-sync mdjourney-backend/requirements-api.txt mdjourney-backend/requirements-dev.txt
	@echo "Done. Your environment is now in sync."

# Package management
package:
	python mdjourney-backend/scripts/build_package.py

package-clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf mdjourney-webapp/dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

package-check:
	pip install -U build twine check-manifest
	check-manifest
	python -m build
	twine check dist/*

# Production builds
build-docker:
	docker-compose build

# Development builds
build-dev:
	docker-compose -f docker-compose.dev.yml build

# Start production services
up:
	docker-compose up -d

# Start development services
up-dev:
	docker-compose -f docker-compose.dev.yml up -d

# Stop all services
down:
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

# Show logs
logs:
	docker-compose logs -f

# Show development logs
logs-dev:
	docker-compose -f docker-compose.dev.yml logs -f

# Clean up containers and images
clean-docker:
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.dev.yml down -v --rmi all
	docker system prune -f

# Run tests (auto-create venv if needed)
test: venv-install
	$(VENV_DIR)/bin/python manage.py test

# Run unit tests only
test-unit: venv-install
	$(VENV_DIR)/bin/python manage.py test --unit

# Run integration tests only
test-integration: venv-install
	$(VENV_DIR)/bin/python manage.py test --integration

# Run linting
lint: venv-install
	$(VENV_DIR)/bin/python manage.py lint

# Format code
format: venv-install
	$(VENV_DIR)/bin/python manage.py format

# Type checking
type-check: venv-install
	$(VENV_DIR)/bin/mypy mdjourney-backend/app/ mdjourney-backend/routers/ mdjourney-backend/tests/

# Build package
build:
	python -m build

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf mdjourney-webapp/dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
	find . -type d -name ".dvc" -exec rm -rf {} +
	find . -type f -name ".dvcignore" -delete
	find . -type f -name ".coverage" -delete || true
	rm -f coverage.xml || true

# Start services (auto-create venv if needed)
start: venv-install
	$(VENV_DIR)/bin/python manage.py start

# Start backend services only (API + Monitor) - for decoupled architecture
start-backend: venv-install
	$(VENV_DIR)/bin/python manage.py start --backend-only

start-api: venv-install
	$(VENV_DIR)/bin/python manage.py start --api-only

start-monitor: venv-install
	$(VENV_DIR)/bin/python manage.py start --monitor-only

start-frontend:
	python manage.py start --frontend-only

start-gateway: venv-install
	cd mdjourney-gateway && $(VENV_DIR)/bin/python main.py

# Setup development environment (auto-create venv if needed)
setup: venv-install
	cd mdjourney-backend && $(VENV_DIR)/bin/python scripts/setup_config.py

# Setup development environment with venv creation
setup-dev: venv-create venv-install
	cd mdjourney-webapp && npm install
	@echo "Development environment setup complete!"
	@echo "Run 'make start' to start the services."

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/v1/health || echo "API not healthy"
	@curl -f http://localhost:5173 || echo "Frontend not healthy"
	@echo "Health check complete"

# Show running containers
ps:
	docker-compose ps
	docker-compose -f docker-compose.dev.yml ps

# Restart services
restart:
	docker-compose restart

# Restart development services
restart-dev:
	docker-compose -f docker-compose.dev.yml restart

# Shell into API container
shell-api:
	docker-compose exec api bash

# Shell into frontend container
shell-frontend:
	docker-compose exec frontend sh

# Shell into monitor container
shell-monitor:
	docker-compose exec monitor bash

# Pre-commit hooks
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

# Frontend Commands
frontend-install:
	cd mdjourney-webapp && npm ci

frontend-build:
	cd mdjourney-webapp && npm run build

frontend-dev:
	cd mdjourney-webapp && npm run dev

frontend-preview:
	cd mdjourney-webapp && npm run preview

frontend-lint:
	cd mdjourney-webapp && npm run lint

frontend-clean:
	cd mdjourney-webapp && rm -rf dist/ node_modules/.vite/

# Start backend services only (for server deployment)
up-backend:
	docker-compose -f docker-compose.backend.yml up -d

# Start frontend service only
up-frontend:
	docker-compose -f docker-compose.frontend.yml up -d

# Build frontend Docker image
build-frontend-docker:
	docker-compose -f docker-compose.frontend.yml build

# Stop frontend service
down-frontend:
	docker-compose -f docker-compose.frontend.yml down

# Show frontend logs
logs-frontend:
	docker-compose -f docker-compose.frontend.yml logs -f

# Combined Commands
build-all: build frontend-build

dev-all: start-backend frontend-dev

clean-all: clean frontend-clean venv-clean
