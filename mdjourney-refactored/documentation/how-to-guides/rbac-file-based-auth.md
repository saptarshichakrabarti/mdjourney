# RBAC-Based File-Based Authentication

This guide shows how to implement user accounts and authentication using RBAC with a file-based approach, avoiding the need for a database.

## Overview

Instead of a full database-backed user system, we can use:
- **File-based user storage** (JSON/YAML files)
- **RBAC for authorization** (already implemented)
- **API key management** (persisted to files)
- **Integration with external identity providers** (LDAP, OAuth, etc.)

## Advantages

✅ No database required
✅ Simple to deploy and maintain
✅ Easy to version control user accounts
✅ Can integrate with existing identity systems
✅ Lightweight and fast

---

## Understanding Authentication vs Authorization

Before implementing the system, it's crucial to understand two distinct but related security concerns:

### 1. **Authentication** — Proving Who a User Is

Authentication answers: **"Who are you?"**

- Verifies user identity (login credentials, API keys, tokens)
- Establishes trust that the user is who they claim to be
- Examples: username/password, API key validation, JWT token verification

### 2. **Authorization** — Deciding What a User Can Do

Authorization answers: **"What are you allowed to do?"**

- Determines permissions based on authenticated identity
- Uses RBAC (Role-Based Access Control) to enforce policies
- Examples: checking if user has `dataset.read` permission, verifying role membership

### Key Distinction

**Session mechanisms** (server-side sessions, JWTs) and **tokens** are **transport/mechanism choices** for carrying authentication state between client and server. They do **not** replace RBAC — RBAC is the **policy model** used by your application to decide access once identity is known.

**Flow:**
1. Client authenticates → receives authentication artifact (session cookie or token)
2. Client makes request → includes authentication artifact
3. Server authenticates request → resolves identity → user_id
4. Server retrieves effective roles/permissions → **RBAC/ACL check**
5. Server enforces permission → allows or denies access

---

## Authorization Model: Hybrid RBAC with Resource-Level ACLs

For a research metadata system, use **RBAC with resource-level ACLs** (hybrid approach) for clarity and scalability:

### Global Roles (System-Wide)

Used for administrative capabilities across the whole system:
- `admin` — Full system access, user management, configuration
- `curator` — Can manage metadata schemas, publish datasets
- `auditor` — Read-only access to audit logs and system state

### Resource-Scoped Roles (Per Dataset/Project)

Attach these roles to a user for a specific dataset or collection:
- `owner` — Full control over a specific dataset (delete, manage ACLs)
- `editor` — Can modify metadata for a specific dataset
- `viewer` — Read-only access to a specific dataset
- `annotator` — Can add annotations but not modify core metadata

### Permissions (Fine-Grained)

Derived from roles, permissions map to concrete actions:
- `dataset.read` — Read dataset metadata
- `dataset.update` — Modify dataset metadata
- `dataset.delete` — Delete dataset
- `metadata.annotate` — Add annotations
- `metadata.publish` — Publish dataset
- `metadata.edit_schema` — Modify metadata schema
- `audit.view_logs` — View audit logs
- `manage` — Administrative operations (user management, config)

### ACL Entries

Access Control Lists map (user or group) → role on a resource. This lets dataset owners grant collaborators specific roles without changing global roles.

**Principle:** Least-privilege defaults — new users have no access to datasets until explicitly granted.

---

## Session Mechanisms: Server-Side Sessions vs JWTs

### Server-Side Sessions (Cookie-Based)

**How it works:**
- After login, server creates a session record (in Redis or file-based store) and sets a session cookie (`session_id`) in the browser
- On each request, server reads the session store to retrieve identity and roles

**Pros:**
- ✅ Easy to revoke sessions immediately (delete session)
- ✅ No need to embed permissions in token; always read up-to-date roles from storage
- ✅ Simpler to implement short-lived role changes (effective immediately)
- ✅ Good for web apps (browser clients) with strong CSRF controls

**Cons:**
- ❌ Requires server-side state (scales with number of sessions; solved by Redis/shared store)
- ❌ Not ideal if many stateless microservices need to verify tokens without centralized session store

**Cookie Settings:**
- `HttpOnly` — Prevents JavaScript access
- `Secure` — HTTPS only
- `SameSite=Strict` or `Lax` — CSRF protection
- `Path=/`, `Domain` scope as needed
- Short session TTL with refresh on activity; rotate session IDs after privilege elevation

### JWT Access Tokens (Stateless)

**How it works:**
- Server issues a signed JWT containing claims (subject, expiry, possibly roles or permissions)
- Services validate signature and expiry locally, without storage lookup

**Pros:**
- ✅ Stateless verification (no session store needed)
- ✅ Convenient for multi-service/microservice architectures and mobile clients
- ✅ Low latency auth checks

**Cons:**
- ❌ Harder to revoke (need token blacklist or short expiry + refresh tokens)
- ❌ If roles/permissions embedded in JWT, changes in storage are not reflected until token expiry
- ❌ Larger attack surface if token storage on client is insecure

**Common Compromise:**
- Use **short-lived access JWTs** (5–15 minutes) + **long-lived refresh tokens** (rotate and store securely server-side or as HttpOnly Secure cookie)
- This gives stateless verification performance while maintaining control via refresh token revocation

---

## Recommended Secure Architecture (Balanced Approach)

For a web application for researchers, use a **hybrid approach**:

### Architecture Components

1. **Short-lived JWT access tokens** (5–15 min) for API calls
   - Include minimal claims: user id, token id (`tid`), issued-at, expiry
   - **Do not embed full ACLs** — keep tokens lightweight

2. **Refresh token** (longer lifetime, 7–30 days)
   - Stored as **HttpOnly, Secure cookie** (or server-side record associated to cookie)
   - Rotate refresh tokens on use
   - Store hashed refresh token server-side to allow revocation

3. **Server-side refresh store** (file-based or Redis)
   - Tracks active refresh tokens and token identifiers
   - Allows immediate revocation on account disable or role change

4. **On each access-token issuance** (refresh)
   - Fetch current role assignments from storage
   - Include **role names** (not full permissions) in new access token if you want fewer storage calls
   - Prefer short TTL so role changes propagate quickly

### Benefits

- ✅ Fast verification for APIs (validate JWT signature locally)
- ✅ Immediate revocation capability (by invalidating refresh token)
- ✅ Up-to-date authorization by forcing short-lived tokens and refreshing when necessary

---

## Token Shapes and Claims (Example)

### Access Token (JWT) — Short Lived

```json
{
  "iss": "https://auth.mdjourney.org",
  "sub": "user:admin",
  "aud": "metadata-api",
  "iat": 1699990000,
  "exp": 1699990900,          // short expiry (e.g., 10m)
  "tid": "uuid-token-id-1",   // unique token id for tracking
  "roles": ["curator"]        // optional: minimal set of global roles
}
```

### Refresh Token

Opaque string stored in cookie; hashed and stored server-side in file-based storage:

```yaml
refresh_tokens:
  <hashed-token-1>:
    user_id: admin
    expires_at: '2024-02-01T00:00:00'
    last_used_at: '2024-01-15T10:30:00'
    revoked: false
    device_info: 'Mozilla/5.0...'
```

---

## Revocation Strategies

### Refresh Token Revocation
- **Immediate**: Delete or mark `revoked=true` in storage
- New access tokens cannot be obtained

### Access Token Revocation
- Since access tokens are short-lived, rely on expiry
- If you must revoke instantly, maintain a small **revocation list** (e.g., file-based set of revoked token ids `tid`) that API gateways check (only for high-risk tokens)

### Role Change Propagation
- If you embed roles in access token, force user to re-authenticate or rotate their tokens when an admin changes their roles
- Alternatively, do not embed roles and check storage for permissions per request (cache results aggressively)

---

## Secure Storage of Tokens on Client

### Web Single-Page App (Browser)
- Store refresh token in `HttpOnly, Secure` cookie
- Store access token in **memory only** (not localStorage)
- Use CSRF tokens for state-changing requests or set `SameSite` appropriately

### Server-Rendered Web App
- Use server-side sessions (cookie) where the cookie is an opaque session id (HttpOnly, Secure)

### Native Apps / Non-Browser Clients
- Store tokens in secure storage (OS keychain)
- Use PKCE where applicable

---

## CSRF and CORS Protection

### CSRF Protection
- If using cookies for auth (session cookie or refresh cookie), protect against CSRF:
  - Use `SameSite=Strict`/`Lax` where possible
  - Implement CSRF tokens for state-changing requests (double-submit cookie if SPA)

### CORS
- For JWT in Authorization header, CSRF risk is low (not sent automatically by browser)
- CORS rules must be configured safely:
  - Only allow trusted origins
  - Use credentials only when necessary
  - Set appropriate `Access-Control-Allow-Headers`

## Implementation

### Phase 0: Enhanced Data Model (File-Based Schema)

The file-based storage schema should support both global roles and resource-scoped ACLs:

```yaml
# .mdjourney_users.yaml structure
users:
  admin:
    username: admin
    email: admin@localhost
    full_name: Administrator
    global_roles:          # System-wide roles
      - admin
    is_active: true
    api_key: <secure-random-token>
    password_hash: <optional-for-future-password-auth>
    created_at: '2024-01-01T00:00:00'
    last_login: '2024-01-15T10:30:00'

  researcher:
    username: researcher
    email: researcher@example.com
    full_name: Research User
    global_roles:
      - viewer
    resource_roles:        # Resource-scoped roles (ACLs)
      datasets:
        dataset-123:
          - editor
        dataset-456:
          - viewer
      projects:
        project-789:
          - owner
    is_active: true
    api_key: <secure-random-token>
    created_at: '2024-01-02T00:00:00'
    last_login: null

# Refresh tokens (for JWT-based auth)
refresh_tokens:
  <hashed-refresh-token-1>:
    user_id: admin
    expires_at: '2024-02-01T00:00:00'
    last_used_at: '2024-01-15T10:30:00'
    revoked: false
    device_info: 'Mozilla/5.0...'

# Revoked token IDs (for access token revocation)
revoked_tokens:
  - uuid-token-id-1
  - uuid-token-id-2

# API key mapping
api_keys:
  <api-key-1>: admin
  <api-key-2>: researcher

updated_at: '2024-01-15T10:30:00'
```

### Phase 1: File-Based User Storage

#### 1.1 Create User Storage Module

Create `mdjourney-backend/app/core/user_storage.py`:

```python
"""
File-based user storage for RBAC authentication.
Stores users in JSON/YAML files for easy management.
"""
import json
import secrets
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from app.core.exceptions import SecurityError, AuthenticationError


class FileBasedUserStorage:
    """Manages users stored in files."""

    def __init__(self, users_file: Optional[Path] = None):
        """
        Initialize user storage.

        Args:
            users_file: Path to users file (default: .mdjourney_users.yaml)
        """
        if users_file is None:
            # Default to config directory or current directory
            from app.core.config import find_config_file
            config_file = find_config_file()
            if config_file:
                users_file = config_file.parent / ".mdjourney_users.yaml"
            else:
                users_file = Path(".mdjourney_users.yaml")

        self.users_file = Path(users_file)
        self._users: Dict[str, Dict] = {}
        self._api_keys: Dict[str, str] = {}  # api_key -> username mapping
        self._load_users()

    def _load_users(self):
        """Load users from file."""
        if not self.users_file.exists():
            # Create default admin user if file doesn't exist
            self._create_default_admin()
            return

        try:
            with open(self.users_file, 'r') as f:
                if self.users_file.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)

            self._users = data.get('users', {})
            self._api_keys = data.get('api_keys', {})

            # Build reverse mapping
            for username, user_data in self._users.items():
                if 'api_key' in user_data:
                    self._api_keys[user_data['api_key']] = username
        except Exception as e:
            raise SecurityError(f"Failed to load users file: {e}")

    def _save_users(self):
        """Save users to file."""
        try:
            data = {
                'users': self._users,
                'api_keys': self._api_keys,
                'updated_at': datetime.utcnow().isoformat()
            }

            # Create backup
            if self.users_file.exists():
                backup_file = self.users_file.with_suffix('.yaml.bak')
                import shutil
                shutil.copy(self.users_file, backup_file)

            with open(self.users_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            # Set restrictive permissions (owner read/write only)
            import os
            os.chmod(self.users_file, 0o600)
        except Exception as e:
            raise SecurityError(f"Failed to save users file: {e}")

    def _create_default_admin(self):
        """Create default admin user."""
        default_api_key = secrets.token_urlsafe(32)
        self._users['admin'] = {
            'username': 'admin',
            'email': 'admin@localhost',
            'full_name': 'Administrator',
            'roles': ['admin'],
            'is_active': True,
            'api_key': default_api_key,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None
        }
        self._api_keys[default_api_key] = 'admin'
        self._save_users()
        print(f"Created default admin user. API key: {default_api_key}")
        print("IMPORTANT: Save this API key securely and change it after first login!")

    def create_user(
        self,
        username: str,
        email: str,
        roles: List[str],
        full_name: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict:
        """
        Create a new user.

        Args:
            username: Username
            email: Email address
            roles: List of roles
            full_name: Full name (optional)
            api_key: API key (generated if not provided)

        Returns:
            User dictionary with API key
        """
        if username in self._users:
            raise AuthenticationError(f"User '{username}' already exists")

        if api_key is None:
            api_key = secrets.token_urlsafe(32)

        if api_key in self._api_keys:
            raise AuthenticationError("API key already in use")

        user_data = {
            'username': username,
            'email': email,
            'full_name': full_name or username,
            'roles': roles,
            'is_active': True,
            'api_key': api_key,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None
        }

        self._users[username] = user_data
        self._api_keys[api_key] = username
        self._save_users()

        return user_data

    def get_user_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Get user by API key."""
        username = self._api_keys.get(api_key)
        if not username:
            return None

        user = self._users.get(username)
        if user and user.get('is_active', True):
            # Update last login
            user['last_login'] = datetime.utcnow().isoformat()
            self._save_users()
            return user

        return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        return self._users.get(username)

    def update_user_roles(self, username: str, roles: List[str]) -> Dict:
        """Update user roles."""
        if username not in self._users:
            raise AuthenticationError(f"User '{username}' not found")

        self._users[username]['roles'] = roles
        self._save_users()
        return self._users[username]

    def regenerate_api_key(self, username: str) -> str:
        """Regenerate API key for a user."""
        if username not in self._users:
            raise AuthenticationError(f"User '{username}' not found")

        old_api_key = self._users[username].get('api_key')
        if old_api_key and old_api_key in self._api_keys:
            del self._api_keys[old_api_key]

        new_api_key = secrets.token_urlsafe(32)
        self._users[username]['api_key'] = new_api_key
        self._api_keys[new_api_key] = username
        self._save_users()

        return new_api_key

    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user account."""
        if username not in self._users:
            return False

        self._users[username]['is_active'] = False
        self._save_users()
        return True

    def list_users(self) -> List[Dict]:
        """List all users (without API keys)."""
        return [
            {k: v for k, v in user.items() if k != 'api_key'}
            for user in self._users.values()
        ]

    def get_effective_roles(self, username: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None) -> List[str]:
        """
        Get effective roles for a user, combining global and resource-scoped roles.

        Args:
            username: Username
            resource_type: Resource type ('datasets', 'projects', etc.) or None for global
            resource_id: Resource ID or None for global

        Returns:
            List of effective roles
        """
        user = self._users.get(username)
        if not user or not user.get('is_active', True):
            return []

        roles = list(user.get('global_roles', user.get('roles', [])))  # Backward compat

        # Add resource-scoped roles if resource specified
        if resource_type and resource_id:
            resource_roles = user.get('resource_roles', {})
            resource_type_roles = resource_roles.get(resource_type, {})
            resource_roles_list = resource_type_roles.get(resource_id, [])
            roles.extend(resource_roles_list)

        return list(set(roles))  # Remove duplicates

    def grant_resource_role(self, username: str, resource_type: str, resource_id: str, role: str) -> Dict:
        """
        Grant a resource-scoped role to a user.

        Args:
            username: Username
            resource_type: Resource type ('datasets', 'projects', etc.)
            resource_id: Resource ID
            role: Role to grant ('owner', 'editor', 'viewer', 'annotator')

        Returns:
            Updated user dictionary
        """
        if username not in self._users:
            raise AuthenticationError(f"User '{username}' not found")

        if 'resource_roles' not in self._users[username]:
            self._users[username]['resource_roles'] = {}

        if resource_type not in self._users[username]['resource_roles']:
            self._users[username]['resource_roles'][resource_type] = {}

        if resource_id not in self._users[username]['resource_roles'][resource_type]:
            self._users[username]['resource_roles'][resource_type][resource_id] = []

        if role not in self._users[username]['resource_roles'][resource_type][resource_id]:
            self._users[username]['resource_roles'][resource_type][resource_id].append(role)

        self._save_users()
        return self._users[username]

    def revoke_resource_role(self, username: str, resource_type: str, resource_id: str, role: str) -> Dict:
        """Revoke a resource-scoped role from a user."""
        if username not in self._users:
            raise AuthenticationError(f"User '{username}' not found")

        resource_roles = self._users[username].get('resource_roles', {})
        resource_type_roles = resource_roles.get(resource_type, {})
        resource_roles_list = resource_type_roles.get(resource_id, [])

        if role in resource_roles_list:
            resource_roles_list.remove(role)
            self._save_users()

        return self._users[username]
```

#### 1.2 Update APIKeyManager to Use File Storage

Update `mdjourney-backend/app/core/auth.py`:

```python
# Add at the top
from app.core.user_storage import FileBasedUserStorage

# Update APIKeyManager
class APIKeyManager:
    """Manages API keys for authentication."""

    def __init__(self):
        self._api_keys: Dict[str, Dict] = {}
        self._user_storage = None
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from file storage or environment."""
        # Try file-based storage first
        try:
            self._user_storage = FileBasedUserStorage()
            # Load all users and their API keys
            for username, user_data in self._user_storage._users.items():
                if user_data.get('is_active') and 'api_key' in user_data:
                    api_key = user_data['api_key']
                    self._api_keys[api_key] = {
                        'id': username,
                        'name': user_data.get('full_name', username),
                        'email': user_data.get('email', ''),
                        'roles': user_data.get('roles', ['viewer']),
                        'created_at': datetime.fromisoformat(user_data.get('created_at', datetime.utcnow().isoformat())),
                        'last_used': datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
                    }
            return
        except Exception as e:
            logger.warning(f"File-based user storage not available: {e}")

        # Fallback to environment variable
        api_key = os.getenv('MDJOURNEY_API_KEY')
        if api_key:
            self._api_keys[api_key] = {
                'name': 'default',
                'roles': ['admin'],
                'created_at': datetime.utcnow(),
                'last_used': None
            }

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key."""
        # Check in-memory cache first
        if api_key in self._api_keys:
            key_info = self._api_keys[api_key]
            key_info['last_used'] = datetime.utcnow()
            return key_info

        # Try to reload from file storage
        if self._user_storage:
            user = self._user_storage.get_user_by_api_key(api_key)
            if user:
                # Add to cache
                key_info = {
                    'id': user['username'],
                    'name': user.get('full_name', user['username']),
                    'email': user.get('email', ''),
                    'roles': user.get('roles', ['viewer']),
                    'created_at': datetime.fromisoformat(user.get('created_at', datetime.utcnow().isoformat())),
                    'last_used': datetime.utcnow()
                }
                self._api_keys[api_key] = key_info
                return key_info

        return None

    def generate_api_key(self, name: str, roles: List[str]) -> str:
        """Generate a new API key."""
        if self._user_storage:
            # Generate username from name
            username = name.lower().replace(' ', '_')
            email = f"{username}@localhost"
            user = self._user_storage.create_user(
                username=username,
                email=email,
                roles=roles,
                full_name=name
            )
            return user['api_key']
        else:
            # Fallback to in-memory
            api_key = secrets.token_urlsafe(32)
            self._api_keys[api_key] = {
                'name': name,
                'roles': roles,
                'created_at': datetime.utcnow(),
                'last_used': None
            }
            return api_key
```

### Phase 1.3: Enhanced RBAC with Resource-Scoped Permissions

Update `mdjourney-backend/app/core/auth.py` to support resource-scoped permissions:

```python
class RoleBasedAccessControl:
    """Handles role-based access control with resource-scoped permissions."""

    # Global roles and their permissions
    GLOBAL_ROLES = {
        'admin': {
            'permissions': ['read', 'write', 'delete', 'manage'],
            'description': 'Full access to all operations'
        },
        'curator': {
            'permissions': ['read', 'write', 'metadata.publish', 'metadata.edit_schema'],
            'description': 'Can manage metadata schemas and publish datasets'
        },
        'auditor': {
            'permissions': ['read', 'audit.view_logs'],
            'description': 'Read-only access to audit logs and system state'
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

    # Resource-scoped roles and their permissions
    RESOURCE_ROLES = {
        'owner': {
            'permissions': ['dataset.read', 'dataset.update', 'dataset.delete', 'metadata.annotate', 'metadata.publish'],
            'description': 'Full control over a specific dataset'
        },
        'editor': {
            'permissions': ['dataset.read', 'dataset.update', 'metadata.annotate'],
            'description': 'Can modify metadata for a specific dataset'
        },
        'viewer': {
            'permissions': ['dataset.read'],
            'description': 'Read-only access to a specific dataset'
        },
        'annotator': {
            'permissions': ['dataset.read', 'metadata.annotate'],
            'description': 'Can add annotations but not modify core metadata'
        }
    }

    # Permission mapping (permission -> required role)
    PERMISSION_MAP = {
        'dataset.read': ['read', 'dataset.read'],
        'dataset.update': ['write', 'dataset.update'],
        'dataset.delete': ['delete', 'dataset.delete'],
        'metadata.annotate': ['write', 'metadata.annotate'],
        'metadata.publish': ['metadata.publish'],
        'metadata.edit_schema': ['metadata.edit_schema'],
        'audit.view_logs': ['audit.view_logs'],
        'manage': ['manage']
    }

    @classmethod
    def has_permission(cls, user_roles: List[str], required_permission: str,
                      resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                      user_storage: Optional[object] = None, username: Optional[str] = None) -> bool:
        """
        Check if user has required permission, considering both global and resource-scoped roles.

        Args:
            user_roles: List of user's global roles
            required_permission: Required permission
            resource_type: Resource type (e.g., 'datasets')
            resource_id: Resource ID
            user_storage: FileBasedUserStorage instance (for resource-scoped checks)
            username: Username (for resource-scoped checks)

        Returns:
            True if user has permission, False otherwise
        """
        # Check global roles first
        for role in user_roles:
            if role in cls.GLOBAL_ROLES:
                if required_permission in cls.GLOBAL_ROLES[role]['permissions']:
                    return True

        # Check resource-scoped roles if resource specified
        if resource_type and resource_id and user_storage and username:
            effective_roles = user_storage.get_effective_roles(username, resource_type, resource_id)
            for role in effective_roles:
                if role in cls.RESOURCE_ROLES:
                    if required_permission in cls.RESOURCE_ROLES[role]['permissions']:
                        return True

        return False

    @classmethod
    def get_permissions_for_roles(cls, roles: List[str], resource_type: Optional[str] = None) -> Set[str]:
        """Get all permissions for a set of roles."""
        permissions = set()

        for role in roles:
            if role in cls.GLOBAL_ROLES:
                permissions.update(cls.GLOBAL_ROLES[role]['permissions'])
            if resource_type and role in cls.RESOURCE_ROLES:
                permissions.update(cls.RESOURCE_ROLES[role]['permissions'])

        return permissions
```

### Phase 2: JWT and Refresh Token Support (Optional Enhancement)

For applications requiring JWT-based authentication, add JWT support:

Create `mdjourney-backend/app/core/jwt_auth.py`:

```python
"""
JWT-based authentication with refresh tokens.
"""
import os
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from fastapi import HTTPException, status
from app.core.user_storage import FileBasedUserStorage

# JWT settings
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


class JWTAuthManager:
    """Manages JWT access tokens and refresh tokens."""

    def __init__(self, user_storage: FileBasedUserStorage):
        self.user_storage = user_storage

    def create_access_token(self, username: str, roles: List[str], token_id: str) -> str:
        """Create a short-lived JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "iss": "mdjourney",
            "sub": f"user:{username}",
            "aud": "metadata-api",
            "iat": datetime.utcnow(),
            "exp": expire,
            "tid": token_id,
            "roles": roles
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def create_refresh_token(self, username: str, device_info: str = "") -> Tuple[str, str]:
        """
        Create a refresh token and store it server-side.
        Returns (refresh_token, hashed_token)
        """
        refresh_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()

        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # Store refresh token in user storage
        refresh_tokens = self.user_storage._load_refresh_tokens()
        refresh_tokens[hashed_token] = {
            'user_id': username,
            'expires_at': expires_at.isoformat(),
            'last_used_at': datetime.utcnow().isoformat(),
            'revoked': False,
            'device_info': device_info
        }
        self.user_storage._save_refresh_tokens(refresh_tokens)

        return refresh_token, hashed_token

    def validate_access_token(self, token: str) -> Optional[Dict]:
        """Validate and decode an access token."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM],
                               audience="metadata-api")

            # Check revocation list
            if self.user_storage.is_token_revoked(payload.get('tid')):
                return None

            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        Validate refresh token and issue new access token.
        Returns (access_token, new_refresh_token) or None if invalid.
        """
        hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
        refresh_tokens = self.user_storage._load_refresh_tokens()

        token_data = refresh_tokens.get(hashed_token)
        if not token_data:
            return None

        if token_data.get('revoked') or datetime.fromisoformat(token_data['expires_at']) < datetime.utcnow():
            return None

        username = token_data['user_id']
        user = self.user_storage.get_user_by_username(username)
        if not user or not user.get('is_active'):
            return None

        # Rotate refresh token
        new_refresh_token, new_hashed = self.create_refresh_token(username, token_data.get('device_info', ''))

        # Revoke old refresh token
        refresh_tokens[hashed_token]['revoked'] = True
        self.user_storage._save_refresh_tokens(refresh_tokens)

        # Create new access token
        token_id = secrets.token_urlsafe(16)
        roles = user.get('global_roles', user.get('roles', []))
        access_token = self.create_access_token(username, roles, token_id)

        return access_token, new_refresh_token

    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""
        hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
        refresh_tokens = self.user_storage._load_refresh_tokens()

        if hashed_token in refresh_tokens:
            refresh_tokens[hashed_token]['revoked'] = True
            self.user_storage._save_refresh_tokens(refresh_tokens)
            return True
        return False
```

### Phase 3: User Management Endpoints

Create `mdjourney-backend/routers/user_management.py`:

```python
"""
User management endpoints for RBAC-based authentication.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.auth import get_current_user, api_key_manager, RoleBasedAccessControl
from app.core.user_storage import FileBasedUserStorage

router = APIRouter(prefix="/users", tags=["user management"])

user_storage = FileBasedUserStorage()


class UserCreate(BaseModel):
    """User creation request."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    roles: List[str] = ["viewer"]


class UserResponse(BaseModel):
    """User response model."""
    username: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    is_active: bool
    created_at: str
    last_login: Optional[str]


class UserWithApiKey(UserResponse):
    """User response with API key (for creation)."""
    api_key: str


@router.post("/", response_model=UserWithApiKey, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new user account (admin only)."""
    # Check permission
    if not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. 'manage' permission required."
        )

    # Validate roles
    valid_roles = ['admin', 'editor', 'viewer']
    for role in user_data.roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Valid roles: {', '.join(valid_roles)}"
            )

    try:
        user = user_storage.create_user(
            username=user_data.username,
            email=user_data.email,
            roles=user_data.roles,
            full_name=user_data.full_name
        )

        return {
            "username": user['username'],
            "email": user['email'],
            "full_name": user.get('full_name'),
            "roles": user['roles'],
            "is_active": user['is_active'],
            "created_at": user['created_at'],
            "last_login": user.get('last_login'),
            "api_key": user['api_key']
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(get_current_user)
):
    """List all users (admin only)."""
    if not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    users = user_storage.list_users()
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information."""
    username = current_user.get('id') or current_user.get('name', '')
    user = user_storage.get_user_by_username(username)

    if not user:
        # Return info from current_user if not in storage
        return {
            "username": current_user.get('name', 'unknown'),
            "email": current_user.get('email', ''),
            "full_name": current_user.get('name', ''),
            "roles": current_user.get('roles', []),
            "is_active": True,
            "created_at": current_user.get('created_at', datetime.utcnow()).isoformat(),
            "last_login": None
        }

    return {
        "username": user['username'],
        "email": user['email'],
        "full_name": user.get('full_name'),
        "roles": user['roles'],
        "is_active": user['is_active'],
        "created_at": user['created_at'],
        "last_login": user.get('last_login')
    }


@router.put("/{username}/roles", response_model=UserResponse)
async def update_user_roles(
    username: str,
    roles: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Update user roles (admin only)."""
    if not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Validate roles
    valid_roles = ['admin', 'editor', 'viewer']
    for role in roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )

    user = user_storage.update_user_roles(username, roles)
    return {
        "username": user['username'],
        "email": user['email'],
        "full_name": user.get('full_name'),
        "roles": user['roles'],
        "is_active": user['is_active'],
        "created_at": user['created_at'],
        "last_login": user.get('last_login')
    }


@router.post("/{username}/regenerate-api-key")
async def regenerate_api_key(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """Regenerate API key for a user."""
    # Users can regenerate their own key, admins can regenerate any key
    if username != current_user.get('id') and not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    new_api_key = user_storage.regenerate_api_key(username)

    # Update API key manager cache
    api_key_manager._load_api_keys()

    return {"api_key": new_api_key}
```

### Phase 4: Authorization Middleware Examples

Create `mdjourney-backend/app/core/middleware.py`:

```python
"""
Authorization middleware for permission checks.
"""
from typing import Callable, Optional
from fastapi import HTTPException, status, Request
from app.core.auth import RoleBasedAccessControl, get_current_user
from app.core.user_storage import FileBasedUserStorage

user_storage = FileBasedUserStorage()


async def require_permission(permission: str, resource_type: Optional[str] = None):
    """
    Dependency factory for requiring specific permission.

    Usage:
        @router.get("/datasets/{dataset_id}")
        async def get_dataset(
            dataset_id: str,
            current_user: dict = Depends(get_current_user),
            _: None = Depends(require_permission('dataset.read', 'datasets'))
        ):
            ...
    """
    async def permission_check(
        current_user: dict = Depends(get_current_user),
        request: Request = None
    ) -> None:
        username = current_user.get('id') or current_user.get('name', '')
        user_roles = current_user.get('roles', [])

        # Extract resource_id from path if resource_type specified
        resource_id = None
        if resource_type and request:
            # Try to extract from path parameters
            if hasattr(request, 'path_params'):
                resource_id = request.path_params.get(f'{resource_type[:-1]}_id')  # e.g., 'dataset_id'

        has_perm = RoleBasedAccessControl.has_permission(
            user_roles=user_roles,
            required_permission=permission,
            resource_type=resource_type,
            resource_id=resource_id,
            user_storage=user_storage,
            username=username
        )

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )

    return permission_check


def check_resource_permission(permission: str, resource_type: str, resource_id: str):
    """
    Decorator for checking resource-scoped permissions.

    Usage:
        @check_resource_permission('dataset.update', 'datasets', 'dataset_id')
        async def update_dataset(dataset_id: str, ...):
            ...
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract current_user from dependencies
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            username = current_user.get('id') or current_user.get('name', '')
            user_roles = current_user.get('roles', [])

            # Extract resource_id from function arguments
            resource_id_value = kwargs.get(resource_id)

            has_perm = RoleBasedAccessControl.has_permission(
                user_roles=user_roles,
                required_permission=permission,
                resource_type=resource_type,
                resource_id=resource_id_value,
                user_storage=user_storage,
                username=username
            )

            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Phase 5: Audit Logging

Add audit logging to track access decisions and sensitive operations:

Create `mdjourney-backend/app/core/audit.py`:

```python
"""
Audit logging for security and compliance.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from app.core.user_storage import FileBasedUserStorage

class AuditLogger:
    """File-based audit logger."""

    def __init__(self, audit_file: Optional[Path] = None):
        if audit_file is None:
            from app.core.config import find_config_file
            config_file = find_config_file()
            if config_file:
                audit_file = config_file.parent / ".mdjourney_audit.log"
            else:
                audit_file = Path(".mdjourney_audit.log")

        self.audit_file = Path(audit_file)

    def log(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict] = None
    ):
        """
        Log an audit event.

        Args:
            user_id: User identifier
            action: Action performed (e.g., 'dataset.read', 'user.create', 'metadata.publish')
            resource_type: Type of resource (e.g., 'datasets', 'users')
            resource_id: Resource identifier
            ip_address: Client IP address
            success: Whether action succeeded
            details: Additional details
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': ip_address,
            'success': success,
            'details': details or {}
        }

        # Append to audit log file
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def query_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query audit logs."""
        if not self.audit_file.exists():
            return []

        logs = []
        with open(self.audit_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())

                    # Filter
                    if user_id and entry.get('user_id') != user_id:
                        continue
                    if action and entry.get('action') != action:
                        continue
                    if resource_type and entry.get('resource_type') != resource_type:
                        continue
                    if resource_id and entry.get('resource_id') != resource_id:
                        continue

                    logs.append(entry)
                except json.JSONDecodeError:
                    continue

        return logs[-limit:]  # Return most recent entries


# Global audit logger instance
audit_logger = AuditLogger()
```

### Phase 6: Add Router to Main App

Update `mdjourney-backend/main.py`:

```python
# Add import
from routers.user_management import router as user_router

# Add router
app.include_router(user_router)
```

### Phase 7: Resource ACL Management Endpoints

Add endpoints for managing resource-scoped ACLs:

```python
# In routers/user_management.py

@router.post("/{username}/resources/{resource_type}/{resource_id}/roles")
async def grant_resource_role(
    username: str,
    resource_type: str,
    resource_id: str,
    role: str,
    current_user: dict = Depends(get_current_user)
):
    """Grant a resource-scoped role to a user."""
    # Check permission: user must be resource owner or admin
    if not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        # Check if current_user is owner of the resource
        effective_roles = user_storage.get_effective_roles(
            current_user.get('id'), resource_type, resource_id
        )
        if 'owner' not in effective_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

    user = user_storage.grant_resource_role(username, resource_type, resource_id, role)

    # Audit log
    from app.core.audit import audit_logger
    audit_logger.log(
        user_id=current_user.get('id'),
        action='acl.grant_role',
        resource_type=resource_type,
        resource_id=resource_id,
        details={'target_user': username, 'role': role}
    )

    return {"message": f"Granted {role} role to {username} on {resource_type}/{resource_id}"}


@router.delete("/{username}/resources/{resource_type}/{resource_id}/roles/{role}")
async def revoke_resource_role(
    username: str,
    resource_type: str,
    resource_id: str,
    role: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke a resource-scoped role from a user."""
    # Similar permission check as above
    if not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        effective_roles = user_storage.get_effective_roles(
            current_user.get('id'), resource_type, resource_id
        )
        if 'owner' not in effective_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

    user = user_storage.revoke_resource_role(username, resource_type, resource_id, role)

    # Audit log
    from app.core.audit import audit_logger
    audit_logger.log(
        user_id=current_user.get('id'),
        action='acl.revoke_role',
        resource_type=resource_type,
        resource_id=resource_id,
        details={'target_user': username, 'role': role}
    )

    return {"message": f"Revoked {role} role from {username} on {resource_type}/{resource_id}"}
```

### Phase 8: CLI Tool for User Management

Create `mdjourney-backend/scripts/manage_users.py`:

```python
#!/usr/bin/env python3
"""CLI tool for managing users."""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.user_storage import FileBasedUserStorage


def main():
    parser = argparse.ArgumentParser(description="Manage MDJourney users")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create user
    create_parser = subparsers.add_parser('create', help='Create a new user')
    create_parser.add_argument('username', help='Username')
    create_parser.add_argument('email', help='Email address')
    create_parser.add_argument('--full-name', help='Full name')
    create_parser.add_argument('--roles', nargs='+', default=['viewer'],
                               choices=['admin', 'editor', 'viewer'],
                               help='User roles')

    # List users
    list_parser = subparsers.add_parser('list', help='List all users')

    # Regenerate API key
    regen_parser = subparsers.add_parser('regenerate-key', help='Regenerate API key')
    regen_parser.add_argument('username', help='Username')

    # Update roles
    roles_parser = subparsers.add_parser('update-roles', help='Update user roles')
    roles_parser.add_argument('username', help='Username')
    roles_parser.add_argument('roles', nargs='+', choices=['admin', 'editor', 'viewer'])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    storage = FileBasedUserStorage()

    try:
        if args.command == 'create':
            user = storage.create_user(
                username=args.username,
                email=args.email,
                roles=args.roles,
                full_name=args.full_name
            )
            print(f"User '{args.username}' created successfully!")
            print(f"API Key: {user['api_key']}")
            print("IMPORTANT: Save this API key securely!")

        elif args.command == 'list':
            users = storage.list_users()
            print(f"\n{'Username':<20} {'Email':<30} {'Roles':<20} {'Active':<10}")
            print("-" * 80)
            for user in users:
                roles_str = ', '.join(user['roles'])
                active = 'Yes' if user['is_active'] else 'No'
                print(f"{user['username']:<20} {user['email']:<30} {roles_str:<20} {active:<10}")

        elif args.command == 'regenerate-key':
            new_key = storage.regenerate_api_key(args.username)
            print(f"New API key for '{args.username}': {new_key}")
            print("IMPORTANT: Update any applications using the old key!")

        elif args.command == 'update-roles':
            user = storage.update_user_roles(args.username, args.roles)
            print(f"Updated roles for '{args.username}': {', '.join(user['roles'])}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
```

## Usage

### 1. Create Users via CLI

```bash
# Create admin user
python scripts/manage_users.py create admin admin@example.com --roles admin --full-name "Administrator"

# Create editor user
python scripts/manage_users.py create editor editor@example.com --roles editor

# List all users
python scripts/manage_users.py list
```

### 2. Create Users via API

```bash
# Get admin API key first (from .mdjourney_users.yaml or CLI)
ADMIN_KEY="your-admin-api-key"

# Create new user
curl -X POST http://localhost:8000/users/ \
  -H "Authorization: Bearer $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "email": "researcher@example.com",
    "full_name": "Research User",
    "roles": ["editor"]
  }'
```

### 3. Use API Keys

```bash
# Get your API key from user management
API_KEY="your-api-key"

# Make authenticated requests
curl -X GET http://localhost:8000/v1/projects \
  -H "Authorization: Bearer $API_KEY"
```

## Integration with External Identity Providers

### LDAP Integration

You can extend `FileBasedUserStorage` to validate against LDAP:

```python
def authenticate_ldap_user(self, username: str, password: str) -> Optional[Dict]:
    """Authenticate user against LDAP and create/update local user."""
    import ldap

    # LDAP authentication logic
    # ...

    # If authenticated, get roles from LDAP groups
    ldap_groups = get_user_groups_from_ldap(username)
    roles = map_ldap_groups_to_roles(ldap_groups)

    # Create or update local user
    if username not in self._users:
        return self.create_user(username, email, roles)
    else:
        return self.update_user_roles(username, roles)
```

### OAuth Integration

For OAuth providers (Google, GitHub, etc.), you can create users on first login:

```python
def authenticate_oauth_user(self, oauth_token: str, provider: str) -> Dict:
    """Authenticate via OAuth and create/update user."""
    # Validate OAuth token
    user_info = validate_oauth_token(oauth_token, provider)

    username = user_info['username']
    email = user_info['email']
    roles = ['viewer']  # Default role

    # Check if user exists
    if username not in self._users:
        return self.create_user(username, email, roles)
    else:
        # Update last login
        self._users[username]['last_login'] = datetime.utcnow().isoformat()
        self._save_users()
        return self._users[username]
```

## Advantages Over Database Approach

1. **No Database Required**: Works with just file system
2. **Version Control**: User files can be version controlled
3. **Easy Backup**: Just copy the YAML file
4. **Simple Deployment**: No database migrations
5. **Flexible**: Easy to integrate with external systems
6. **RBAC Ready**: Uses existing RBAC infrastructure

## Security Considerations

### File Security

1. **File Permissions**: Users file should be `600` (owner read/write only)
2. **Backup**: Automatic backups created before saves
3. **Audit Log Protection**: Audit logs should be append-only and protected (`600` permissions)

### Token Security

1. **API Key Security**: Cryptographically secure random tokens (`secrets.token_urlsafe(32)`)
2. **JWT Secret Key**: Use strong, randomly generated secret key (store in environment variable)
3. **Token Expiry**: Short-lived access tokens (5-15 min), longer refresh tokens (7-30 days)
4. **Token Rotation**: Rotate refresh tokens on each use
5. **Token Revocation**: Maintain revocation lists for immediate invalidation

### Authentication Security

1. **Password Hashing**: If implementing password auth, use Argon2 or bcrypt (never store plaintext)
2. **Rate Limiting**: Implement rate limiting on login/auth endpoints
3. **Account Lockout**: Lock accounts after failed authentication attempts
4. **HTTPS Only**: Always use HTTPS in production; set `Secure` flag on cookies

### Authorization Security

1. **Role Validation**: Roles are validated against allowed set
2. **Least Privilege**: Default to no access; grant permissions explicitly
3. **Permission Checks**: Always check permissions, never trust client claims
4. **Resource Isolation**: Ensure users can only access resources they're granted access to

### Audit and Monitoring

1. **Audit Trail**: Log all sensitive operations (reads of restricted datasets, writes, publish actions)
2. **Log Retention**: Retain logs as required by policy (research data policies / GDPR considerations)
3. **Immutable Logs**: Use append-only storage for audit logs
4. **Monitoring**: Monitor for suspicious activity (unusual access patterns, privilege escalation attempts)

### Operational Security

1. **Session Management**: Implement session timeout and idle timeout
2. **CSRF Protection**: Use `SameSite` cookies and CSRF tokens
3. **CORS Configuration**: Only allow trusted origins
4. **Input Validation**: Validate all inputs, especially resource IDs and role names
5. **Error Messages**: Don't leak sensitive information in error messages

## File Format

The `.mdjourney_users.yaml` file format:

```yaml
users:
  admin:
    username: admin
    email: admin@localhost
    full_name: Administrator
    roles:
      - admin
    is_active: true
    api_key: <secure-random-token>
    created_at: '2024-01-01T00:00:00'
    last_login: '2024-01-15T10:30:00'
  editor:
    username: editor
    email: editor@example.com
    full_name: Editor User
    roles:
      - editor
    is_active: true
    api_key: <secure-random-token>
    created_at: '2024-01-02T00:00:00'
    last_login: null
api_keys:
  <api-key-1>: admin
  <api-key-2>: editor
updated_at: '2024-01-15T10:30:00'
```

---

## Practical Implementation Checklist

Use this checklist when implementing the authentication and authorization system:

### Design Phase

- [ ] Define roles and permissions, map them to concrete actions in your API
- [ ] Design file-based schema for users, roles, ACLs, and refresh tokens
- [ ] Choose session approach:
  - [ ] Server-side sessions (Redis/file) + session cookie
  - [ ] Short-lived JWT + refresh tokens with server-side revocation store
- [ ] Plan token rotation and revocation strategy
- [ ] Design audit logging requirements

### Implementation Phase

- [ ] Create file-based user storage module
- [ ] Implement global roles and resource-scoped roles
- [ ] Create permission mapping (role → permissions)
- [ ] Implement authentication mechanism (API keys, JWT, or sessions)
- [ ] Implement refresh token storage and rotation
- [ ] Add middleware for auth and authorization
- [ ] Centralize permission checks in authorization library
- [ ] Implement audit logging for sensitive operations
- [ ] Add user management endpoints (CRUD, role management)
- [ ] Add resource ACL management endpoints

### Security Phase

- [ ] Implement secure cookie flags (`HttpOnly`, `Secure`, `SameSite`)
- [ ] Add CSRF protection (tokens or `SameSite` cookies)
- [ ] Configure CORS safely (trusted origins only)
- [ ] Implement rate limiting on auth endpoints
- [ ] Add input validation for all user inputs
- [ ] Set file permissions correctly (`600` for sensitive files)
- [ ] Use HTTPS everywhere in production
- [ ] Implement password hashing if using password auth (Argon2/bcrypt)

### Testing Phase

- [ ] Test role escalation attempts (users trying to grant themselves admin)
- [ ] Test revocation (immediate token invalidation)
- [ ] Test token replay attacks
- [ ] Test resource isolation (users can't access unauthorized resources)
- [ ] Test permission checks on all protected endpoints
- [ ] Test audit logging captures all sensitive operations
- [ ] Test session timeout and refresh token expiry

### Operational Phase

- [ ] Set up monitoring for suspicious activity
- [ ] Configure log retention policies
- [ ] Document token management procedures
- [ ] Create runbooks for common security incidents
- [ ] Regularly review and test: role escalation, revocation, token replay

---

## Example Endpoints (Recommended)

### Authentication Endpoints

- `POST /auth/login` → Issues access token + sets refresh cookie
- `POST /auth/refresh` → Rotates refresh token, issues new access token
- `POST /auth/logout` → Revoke refresh token / destroy session

### Resource Endpoints (with Permission Checks)

- `GET /datasets/:id` → Require `dataset.read` permission
- `PUT /datasets/:id/metadata` → Require `dataset.update` or `metadata.edit` permission
- `POST /datasets/:id/publish` → Require `metadata.publish` permission
- `DELETE /datasets/:id` → Require `dataset.delete` permission (owner or admin)
- `POST /datasets/:id/acl` → Require `owner` role on dataset or `admin` global role

### User Management Endpoints

- `GET /users/me` → Get current user info
- `POST /users` → Create user (admin only, requires `manage` permission)
- `GET /users` → List users (admin only)
- `PUT /users/:username/roles` → Update global roles (admin only)
- `POST /users/:username/resources/:type/:id/roles` → Grant resource role (owner/admin)

---

## Final Notes: Security Best Practices

### Principle of Least Privilege

- Default to no access; grant permissions explicitly
- Use resource-scoped roles to limit access to specific datasets
- Regularly audit and remove unnecessary permissions

### Separation of Duties

- Don't allow users to grant themselves elevated privileges
- Require multiple approvals for sensitive operations (e.g., dataset deletion)
- Separate authentication and authorization concerns

### Defense in Depth

- Use HTTPS everywhere; set `Secure` on cookies
- Implement multiple layers of security (rate limiting, input validation, permission checks)
- Monitor and log all security-relevant events

### Threat Modeling

- Run threat modeling for high-impact flows (publish, delete, role changes)
- Include rate-limiting and anomaly detection for credential abuse
- Plan for common attack vectors (CSRF, XSS, privilege escalation)

### Compliance and Audit

- Maintain immutable audit logs for regulatory compliance
- Retain logs as required by policy (research data policies / GDPR considerations)
- Regularly review audit logs for suspicious activity

---

This approach provides user account management with RBAC and resource-level ACLs without requiring a database, while maintaining security best practices!
