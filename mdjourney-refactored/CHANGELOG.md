# Changelog

All notable changes to the MDJourney FAIR Metadata Automation System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Gateway-based architecture for session-based backend management
- Session management system enabling multiple concurrent user sessions
- Per-session backend instance allocation and lifecycle management
- Configuration file upload and parsing through web interface
- Gateway reverse proxy functionality for request routing
- Support for JSON and YAML configuration file formats
- Configuration key normalization from gateway format to internal format
- Frontend configuration file selection and session initiation
- Docker support for gateway service
- Comprehensive test suite adapted for gateway architecture
- Documentation updates for gateway-based deployment

### Changed

- Refactored architecture from monolithic to gateway-based session management
- API endpoint paths changed from `/api/v1/` to `/v1/` for direct backend access
- Gateway routes requests through `/api/` prefix to backend instances
- Configuration loading logic enhanced to support both JSON and YAML formats
- Sample configuration file updated to match template format
- Test suite updated to reflect new API endpoint structure
- Process management scripts adapted for gateway architecture
- Docker Compose configurations updated for gateway service integration

### Fixed

- Configuration template consistency between sample-config.yaml and fair_meta_config_template.yaml
- Configuration key normalization handling for both camelCase and snake_case formats
- Import paths in test suite for refactored directory structure
- API endpoint references in test fixtures

## [1.0.0] - 2024-01-15

### Added

- Initial release of MDJourney refactored architecture
- Gateway service for session-based backend management
- Backend service with comprehensive metadata management
- Web application with React and TypeScript
- File system monitoring with automatic metadata generation
- Schema resolution system with local override support
- Version control integration (Git and DVC)
- Security features including authentication and rate limiting
- Performance optimizations including caching and async processing
- Docker containerization support
- Comprehensive documentation
- Testing infrastructure

### Architecture Components

- Gateway service managing user sessions and backend instances
- Backend API providing metadata management endpoints
- File system monitor for automatic metadata capture
- Web frontend for user interaction
- Schema management system with dynamic resolution
- Configuration management with environment variable support

### Security Features

- Input validation and sanitization
- Path traversal protection
- Rate limiting on API endpoints
- Optional API key authentication
- Security headers on HTTP responses
- Session-based isolation

### Performance Features

- Asynchronous file processing
- Background task management
- Redis-based caching
- Connection pooling
- Concurrent file operations

## Migration Notes

### From Previous Architecture

Users migrating from the previous monolithic architecture should note:

1. **Configuration Format**: Configuration files now use consistent snake_case format matching the template structure.

2. **API Endpoints**: When accessing the backend directly, endpoints use `/v1/` prefix. Through the gateway, endpoints use `/api/v1/` prefix.

3. **Session Management**: The gateway architecture requires session initialization through the web interface before API access.

4. **Backend Instances**: Backend instances are now spawned per session rather than running as a single service.

5. **Configuration Loading**: The system supports both JSON and YAML configuration formats, with automatic normalization of gateway-style keys.

### Configuration Migration

Existing configuration files should be updated to match the template format:

- Use `monitor_path` instead of `watchDirectory`
- Use `schemas.custom_path` instead of `templateDirectory`
- Use `monitor.ignore_patterns` instead of `watchPatterns`

The system includes automatic normalization for backward compatibility, but using the standard format is recommended.

## Future Roadmap

### Planned Features

- Enhanced session management with persistence
- Multi-user support with role-based access control
- Advanced monitoring and observability
- Integration with external LIMS/ELN systems
- Enhanced performance monitoring and optimization
- Extended schema customization capabilities
- Improved error handling and recovery mechanisms

### Known Limitations

- Session state is currently stored in memory (not persistent across gateway restarts)
- Backend instance cleanup requires manual intervention in some scenarios
- Gateway port allocation is currently limited to a fixed range

---

[Unreleased]: https://github.com/saptarshichakrabarti/mdjourney/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/saptarshichakrabarti/mdjourney/releases/tag/v1.0.0
