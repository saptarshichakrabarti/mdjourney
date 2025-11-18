"""
Authentication and authorization module for the FAIR metadata automation system.
Handles API key authentication and role-based access control.
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from functools import wraps

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.exceptions import SecurityError, AuthenticationError


class APIKeyManager:
    """Manages API keys for authentication."""

    def __init__(self):
        self._api_keys: Dict[str, Dict] = {}
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment variables."""
        # In production, this should load from a secure database
        api_key = os.getenv('MDJOURNEY_API_KEY')
        if api_key:
            self._api_keys[api_key] = {
                'name': 'default',
                'roles': ['admin'],
                'created_at': datetime.utcnow(),
                'last_used': None
            }

    def generate_api_key(self, name: str, roles: List[str]) -> str:
        """
        Generate a new API key.

        Args:
            name: Name/description for the API key
            roles: List of roles for this key

        Returns:
            Generated API key
        """
        api_key = secrets.token_urlsafe(32)
        self._api_keys[api_key] = {
            'name': name,
            'roles': roles,
            'created_at': datetime.utcnow(),
            'last_used': None
        }
        return api_key

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Validate an API key.

        Args:
            api_key: The API key to validate

        Returns:
            Key information if valid, None otherwise
        """
        if api_key in self._api_keys:
            key_info = self._api_keys[api_key]
            key_info['last_used'] = datetime.utcnow()
            return key_info
        return None

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key.

        Args:
            api_key: The API key to revoke

        Returns:
            True if revoked, False if not found
        """
        if api_key in self._api_keys:
            del self._api_keys[api_key]
            return True
        return False


class RoleBasedAccessControl:
    """Handles role-based access control."""

    # Define roles and their permissions
    ROLES = {
        'admin': {
            'permissions': ['read', 'write', 'delete', 'manage'],
            'description': 'Full access to all operations'
        },
        'editor': {
            'permissions': ['read', 'write'],
            'description': 'Can read and modify metadata'
        },
        'viewer': {
            'permissions': ['read'],
            'description': 'Read-only access'
        }
    }

    # Define endpoint permissions
    ENDPOINT_PERMISSIONS = {
        'GET /api/v1/projects': 'read',
        'GET /api/v1/projects/{project_id}/datasets': 'read',
        'GET /api/v1/schemas/contextual': 'read',
        'GET /api/v1/schemas/{schema_type}/{schema_id}': 'read',
        'GET /api/v1/projects/{project_id}/metadata/{metadata_type}': 'read',
        'GET /api/v1/datasets/{dataset_id}/metadata/{metadata_type}': 'read',
        'GET /api/v1/health': 'read',

        'POST /api/v1/rescan': 'manage',
        'PUT /api/v1/projects/{project_id}/metadata/{metadata_type}': 'write',
        'PUT /api/v1/datasets/{dataset_id}/metadata/{metadata_type}': 'write',
        'POST /api/v1/datasets/{dataset_id}/contextual': 'write',
        'POST /api/v1/datasets/{dataset_id}/finalize': 'write',
        'POST /api/v1/config/reload': 'manage',
    }

    @classmethod
    def has_permission(cls, user_roles: List[str], required_permission: str) -> bool:
        """
        Check if user has required permission.

        Args:
            user_roles: List of user roles
            required_permission: Required permission

        Returns:
            True if user has permission, False otherwise
        """
        for role in user_roles:
            if role in cls.ROLES:
                if required_permission in cls.ROLES[role]['permissions']:
                    return True
        return False

    @classmethod
    def get_endpoint_permission(cls, method: str, path: str) -> Optional[str]:
        """
        Get required permission for an endpoint.

        Args:
            method: HTTP method
            path: URL path

        Returns:
            Required permission or None if no permission required
        """
        endpoint_key = f"{method} {path}"
        return cls.ENDPOINT_PERMISSIONS.get(endpoint_key)


# Global instances
api_key_manager = APIKeyManager()
security_scheme = HTTPBearer()


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Dict:
    """
    Get current authenticated user from API key.
    Returns a default user if authentication is disabled.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User information dictionary

    Raises:
        HTTPException: If authentication fails and is enabled
    """
    # Check if authentication is disabled
    if os.getenv('ENABLE_AUTHENTICATION', 'false').lower() == 'false':
        return {
            'name': 'local_user',
            'roles': ['admin'],
            'created_at': datetime.utcnow(),
            'last_used': datetime.utcnow()
        }

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = credentials.credentials
    user_info = api_key_manager.validate_api_key(api_key)

    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_info


def require_permission(permission: str):
    """
    Decorator to require specific permission for an endpoint.

    Args:
        permission: Required permission

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user info from dependencies
            user_info = None
            for arg in args:
                if isinstance(arg, dict) and 'roles' in arg:
                    user_info = arg
                    break

            if not user_info:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )

            if not RoleBasedAccessControl.has_permission(user_info['roles'], permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {permission}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_auth(func):
    """
    Decorator to require authentication for an endpoint.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if user_info is in kwargs
        user_info = kwargs.get('user_info')
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        return await func(*args, **kwargs)
    return wrapper


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


# Optional authentication dependency for endpoints that can work with or without auth
def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict]:
    """
    Get current user if authenticated, None otherwise.
    Returns a default user if authentication is disabled.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        User information dictionary or None
    """
    # Check if authentication is disabled
    if os.getenv('ENABLE_AUTHENTICATION', 'false').lower() == 'false':
        return {
            'name': 'local_user',
            'roles': ['admin'],
            'created_at': datetime.utcnow(),
            'last_used': datetime.utcnow()
        }

    if not credentials:
        return None

    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
