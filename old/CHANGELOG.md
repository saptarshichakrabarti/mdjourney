# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]
### Added
- Compose hardening: read-only FS and tmpfs for API/monitor
- Uvicorn workers and proxy headers in API Dockerfiles
- Expanded .dockerignore and .gitignore

### Changed
- manage.py: switched CLI output from print() to structured logging
- Fixed compose monitor healthcheck mismatch (use image-defined check)
- Dockerfile.api.prod: avoid bundling mutable `data/`
- Removed Redis port publishing from compose (internal only)

## [0.1.0] - 2025-10-28
### Added
- Initial public-ready release of MDJourney core, API, monitor, and frontend
- Packaged schemas and documentation set

[Unreleased]: https://github.com/your-org/mdjourney/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/mdjourney/releases/tag/v0.1.0
