# ACL-Based Authentication and Authorization Guide

This guide explains how to implement Access Control Lists (ACLs) as an alternative to full user account management, addressing the limitations of the current authentication system.

## Overview

ACL-based authentication provides:
- **Persistent API keys** stored in configuration files or external systems
- **User/group management** via external identity providers (LDAP, OAuth, file-based)
- **Password-based authentication** through external providers
- **No database required** - uses files or external services
- **Simpler deployment** - integrates with existing HPC/scientific computing infrastructure

## Current Limitations Addressed

| Limitation | ACL Solution |
|-----------|--------------|
| API keys in-memory | Store in YAML/JSON config files or external key management |
| No user account database | Use external identity providers (LDAP, OAuth, file-based) |
| No password authentication | Integrate with LDAP, OAuth, or simple password file |
| No registration endpoints | Use external user management or admin-managed ACL files |
| No user profiles | Minimal profiles stored in ACL config, full profiles in external system |

## Implementation Strategy

### Phase 1: ACL Configuration System

#### 1.1 ACL Configuration File Structure

Create `mdjourney-backend/app/core/acl.py`:

```python
"""
Access Control List (ACL) management for authentication and authorization.
Supports file-based, LDAP, and OAuth identity providers.
"""
import os
import json
import yaml
import hashlib
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import HTTPException
from app.core.exceptions import SecurityError, AuthenticationError


class IdentityProvider(Enum):
    """Supported identity providers."""
    FILE = "file"  # YAML/JSON file-based
    LDAP = "ldap"  # LDAP/Active Directory
    OAUTH = "oauth"  # OAuth2/OIDC
    ENV = "env"  # Environment variables


@dataclass
class ACLUser:
    """User entry in ACL."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: List[str] = None
    api_key: Optional[str] = None
    password_hash: Optional[str] = None  # For file-based auth
    groups: List[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = ["viewer"]
        if self.groups is None:
            self.groups = []


@dataclass
class ACLGroup:
    """Group entry in ACL."""
    name: str
    roles: List[str]
    members: List[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        if self.members is None:
            self.members = []


class ACLManager:
    """Manages Access Control Lists from configuration files."""

    def __init__(self, acl_file: Optional[Path] = None):
        """
        Initialize ACL manager.

        Args:
            acl_file: Path to ACL configuration file (YAML or JSON)
        """
        self.acl_file = acl_file or self._find_acl_file()
        self.users: Dict[str, ACLUser] = {}
        self.groups: Dict[str, ACLGroup] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> username mapping
        self.identity_provider = IdentityProvider.FILE
        self._load_acl()

    def _find_acl_file(self) -> Optional[Path]:
        """Find ACL configuration file."""
        possible_paths = [
            Path(".mdjourney_acl.yaml"),
            Path(".mdjourney_acl.json"),
            Path("mdjourney-backend/.mdjourney_acl.yaml"),
            Path(os.getenv("MDJOURNEY_ACL_FILE", "")),
        ]

        for path in possible_paths:
            if path and path.exists():
                return path
        return None

    def _load_acl(self):
        """Load ACL from configuration file."""
        if not self.acl_file or not self.acl_file.exists():
            # Load from environment variables as fallback
            self._load_from_env()
            return

        try:
            if self.acl_file.suffix == '.yaml':
                with open(self.acl_file, 'r') as f:
                    data = yaml.safe_load(f)
            else:
                with open(self.acl_file, 'r') as f:
                    data = json.load(f)

            # Load identity provider
            provider = data.get('identity_provider', 'file')
            self.identity_provider = IdentityProvider(provider)

            # Load users
            users_data = data.get('users', [])
            for user_data in users_data:
                user = ACLUser(**user_data)
                self.users[user.username] = user
                if user.api_key:
                    self.api_keys[user.api_key] = user.username

            # Load groups
            groups_data = data.get('groups', [])
            for group_data in groups_data:
                group = ACLGroup(**group_data)
                self.groups[group.name] = group

            # Apply group memberships to users
            self._apply_group_memberships()

        except Exception as e:
            raise SecurityError(f"Failed to load ACL: {e}")

    def _load_from_env(self):
        """Load ACL from environment variables."""
        api_key = os.getenv('MDJOURNEY_API_KEY')
        if api_key:
            user = ACLUser(
                username='default',
                roles=['admin'],
                api_key=api_key,
                created_at=datetime.utcnow().isoformat()
            )
            self.users['default'] = user
            self.api_keys[api_key] = 'default'

    def _apply_group_memberships(self):
        """Apply group roles to users."""
        for group_name, group in self.groups.items():
            for member in group.members:
                if member in self.users:
                    user = self.users[member]
                    # Merge group roles with user roles
                    user.roles = list(set(user.roles + group.roles))

    def _save_acl(self):
        """Save ACL to configuration file."""
        if not self.acl_file:
            return  # Can't save if no file specified

        data = {
            'identity_provider': self.identity_provider.value,
            'users': [asdict(user) for user in self.users.values()],
            'groups': [asdict(group) for group in self.groups.values()],
        }

        try:
            if self.acl_file.suffix == '.yaml':
                with open(self.acl_file, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                with open(self.acl_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            raise SecurityError(f"Failed to save ACL: {e}")

    def authenticate_api_key(self, api_key: str) -> Optional[ACLUser]:
        """Authenticate user by API key."""
        username = self.api_keys.get(api_key)
        if username and username in self.users:
            user = self.users[username]
            if user.is_active:
                # Update last login
                user.last_login = datetime.utcnow().isoformat()
                self._save_acl()
                return user
        return None

    def authenticate_password(self, username: str, password: str) -> Optional[ACLUser]:
        """Authenticate user by username and password."""
        if self.identity_provider == IdentityProvider.LDAP:
            return self._authenticate_ldap(username, password)
        elif self.identity_provider == IdentityProvider.OAUTH:
            raise NotImplementedError("OAuth authentication not yet implemented")
        else:
            return self._authenticate_file(username, password)

    def _authenticate_file(self, username: str, password: str) -> Optional[ACLUser]:
        """Authenticate against file-based password hash."""
        user = self.users.get(username)
        if not user or not user.is_active:
            return None

        if not user.password_hash:
            return None  # No password set

        # Verify password hash
        if self._verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow().isoformat()
            self._save_acl()
            return user
        return None

    def _authenticate_ldap(self, username: str, password: str) -> Optional[ACLUser]:
        """Authenticate against LDAP/Active Directory."""
        try:
            import ldap3
            from ldap3 import Server, Connection, ALL

            ldap_server = os.getenv('LDAP_SERVER', 'ldap://localhost:389')
            ldap_base_dn = os.getenv('LDAP_BASE_DN', 'dc=example,dc=com')
            ldap_user_dn = os.getenv('LDAP_USER_DN', f'uid={username},{ldap_base_dn}')

            server = Server(ldap_server, get_info=ALL)
            conn = Connection(server, ldap_user_dn, password, auto_bind=True)

            if conn.bind():
                # User authenticated, get user info from ACL
                user = self.users.get(username)
                if user:
                    user.last_login = datetime.utcnow().isoformat()
                    return user
                else:
                    # Create user entry if doesn't exist
                    user = ACLUser(
                        username=username,
                        roles=['viewer'],  # Default role
                        last_login=datetime.utcnow().isoformat()
                    )
                    self.users[username] = user
                    self._save_acl()
                    return user

            conn.unbind()
            return None
        except ImportError:
            raise SecurityError("LDAP authentication requires ldap3 package")
        except Exception as e:
            raise AuthenticationError(f"LDAP authentication failed: {e}")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        # Simple hash verification (use bcrypt in production)
        if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
            # bcrypt hash
            try:
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                return pwd_context.verify(password, password_hash)
            except ImportError:
                # Fallback to simple hash
                return hashlib.sha256(password.encode()).hexdigest() == password_hash
        else:
            # Simple SHA256 hash (for backward compatibility)
            return hashlib.sha256(password.encode()).hexdigest() == password_hash

    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.hash(password)
        except ImportError:
            # Fallback to simple hash
            return hashlib.sha256(password.encode()).hexdigest()

    def create_user(
        self,
        username: str,
        password: Optional[str] = None,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        generate_api_key: bool = True
    ) -> ACLUser:
        """Create a new user in ACL."""
        if username in self.users:
            raise SecurityError(f"User {username} already exists")

        api_key = None
        if generate_api_key:
            api_key = secrets.token_urlsafe(32)
            self.api_keys[api_key] = username

        password_hash = None
        if password:
            password_hash = self._hash_password(password)

        user = ACLUser(
            username=username,
            email=email,
            full_name=full_name,
            roles=roles or ["viewer"],
            api_key=api_key,
            password_hash=password_hash,
            created_at=datetime.utcnow().isoformat()
        )

        self.users[username] = user
        self._save_acl()
        return user

    def update_user_roles(self, username: str, roles: List[str]) -> ACLUser:
        """Update user roles."""
        if username not in self.users:
            raise SecurityError(f"User {username} not found")

        user = self.users[username]
        user.roles = roles
        self._save_acl()
        return user

    def regenerate_api_key(self, username: str) -> str:
        """Regenerate API key for a user."""
        if username not in self.users:
            raise SecurityError(f"User {username} not found")

        user = self.users[username]
        # Remove old API key
        if user.api_key:
            self.api_keys.pop(user.api_key, None)

        # Generate new API key
        new_api_key = secrets.token_urlsafe(32)
        user.api_key = new_api_key
        self.api_keys[new_api_key] = username
        self._save_acl()
        return new_api_key

    def get_user_by_api_key(self, api_key: str) -> Optional[ACLUser]:
        """Get user by API key."""
        return self.authenticate_api_key(api_key)

    def get_user_by_username(self, username: str) -> Optional[ACLUser]:
        """Get user by username."""
        return self.users.get(username)

    def list_users(self) -> List[ACLUser]:
        """List all users."""
        return list(self.users.values())

    def create_group(self, name: str, roles: List[str], members: Optional[List[str]] = None) -> ACLGroup:
        """Create a new group."""
        if name in self.groups:
            raise SecurityError(f"Group {name} already exists")

        group = ACLGroup(
            name=name,
            roles=roles,
            members=members or []
        )
        self.groups[name] = group
        self._apply_group_memberships()
        self._save_acl()
        return group


# Global ACL manager instance
_acl_manager: Optional[ACLManager] = None


def get_acl_manager() -> ACLManager:
    """Get global ACL manager instance."""
    global _acl_manager
    if _acl_manager is None:
        _acl_manager = ACLManager()
    return _acl_manager
```

### Phase 2: Update Authentication Module

Update `mdjourney-backend/app/core/auth.py` to use ACLManager:

```python
# Add at the top
from app.core.acl import get_acl_manager, ACLUser

# Update APIKeyManager to use ACL
class APIKeyManager:
    """Manages API keys for authentication."""

    def __init__(self):
        self.acl_manager = get_acl_manager()

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key."""
        user = self.acl_manager.authenticate_api_key(api_key)
        if user:
            return {
                'id': user.username,
                'name': user.username,
                'email': user.email,
                'roles': user.roles,
                'created_at': user.created_at,
                'last_used': user.last_login
            }
        return None

    def generate_api_key(self, name: str, roles: List[str]) -> str:
        """Generate a new API key."""
        user = self.acl_manager.create_user(
            username=name,
            roles=roles,
            generate_api_key=True
        )
        return user.api_key
```

### Phase 3: Create ACL Configuration File

Create `.mdjourney_acl.yaml` in the project root:

```yaml
identity_provider: file  # Options: file, ldap, oauth, env

users:
  - username: admin
    email: admin@example.com
    full_name: Administrator
    roles:
      - admin
    api_key: "your-generated-api-key-here"
    password_hash: "$2b$12$..."  # bcrypt hash
    is_active: true
    created_at: "2024-01-01T00:00:00"

  - username: researcher1
    email: researcher1@example.com
    full_name: Researcher One
    roles:
      - editor
    groups:
      - researchers
    is_active: true

groups:
  - name: researchers
    roles:
      - editor
    members:
      - researcher1
    description: "Research team members"

  - name: data_stewards
    roles:
      - admin
      - editor
    members: []
    description: "Data stewards with full access"
```

### Phase 4: Create ACL Management Endpoints

Create `mdjourney-backend/routers/acl_management.py`:

```python
"""
ACL management endpoints for user and group administration.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.acl import get_acl_manager, ACLUser, ACLGroup
from app.core.auth import get_current_user, RoleBasedAccessControl

router = APIRouter(prefix="/acl", tags=["acl"])


class UserCreate(BaseModel):
    """User creation request."""
    username: str
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    generate_api_key: bool = True


class UserResponse(BaseModel):
    """User response model."""
    username: str
    email: Optional[str]
    full_name: Optional[str]
    roles: List[str]
    api_key: Optional[str]
    is_active: bool
    created_at: Optional[str]
    last_login: Optional[str]


class GroupCreate(BaseModel):
    """Group creation request."""
    name: str
    roles: List[str]
    members: Optional[List[str]] = None
    description: Optional[str] = None


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new user (admin only)."""
    # Check permission
    if not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    acl_manager = get_acl_manager()
    try:
        user = acl_manager.create_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            full_name=user_data.full_name,
            roles=user_data.roles,
            generate_api_key=user_data.generate_api_key
        )
        return UserResponse(**user.__dict__)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(get_current_user)
):
    """List all users (admin only)."""
    if not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    acl_manager = get_acl_manager()
    users = acl_manager.list_users()
    return [UserResponse(**user.__dict__) for user in users]


@router.post("/users/{username}/regenerate-api-key")
async def regenerate_api_key(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """Regenerate API key for a user."""
    # Users can regenerate their own key, admins can regenerate any
    if username != current_user.get('name') and not RoleBasedAccessControl.has_permission(current_user['roles'], 'manage'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    acl_manager = get_acl_manager()
    try:
        new_key = acl_manager.regenerate_api_key(username)
        return {"api_key": new_key}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(username: str, password: str):
    """Login with username and password."""
    acl_manager = get_acl_manager()
    user = acl_manager.authenticate_password(username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    return {
        "api_key": user.api_key,
        "user": UserResponse(**user.__dict__)
    }
```

### Phase 5: Update Frontend for ACL-Based Auth

Update `mdjourney-webapp/src/pages/LoginPage.tsx`:

```typescript
// Add username/password login option alongside config file upload
const [loginMode, setLoginMode] = useState<'config' | 'password'>('password');
const [username, setUsername] = useState('');
const [password, setPassword] = useState('');

const handlePasswordLogin = async () => {
  try {
    const response = await apiClient.post('/acl/login', null, {
      params: { username, password }
    });

    localStorage.setItem('mdjourney_api_key', response.data.api_key);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.api_key}`;

    login();
    navigate('/');
  } catch (e: any) {
    setError(e.response?.data?.detail || 'Login failed');
  }
};
```

## Usage Examples

### 1. Initialize ACL File

```bash
# Create initial ACL file
cat > .mdjourney_acl.yaml << EOF
identity_provider: file

users:
  - username: admin
    email: admin@example.com
    roles: [admin]
    password_hash: "\$2b\$12\$..."  # Generate with: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('password'))"
    generate_api_key: true

groups: []
EOF
```

### 2. Create Users via API

```bash
# Create user (requires admin API key)
curl -X POST http://localhost:8000/acl/users \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher1",
    "password": "securepassword",
    "email": "researcher1@example.com",
    "roles": ["editor"],
    "generate_api_key": true
  }'
```

### 3. Login with Password

```bash
curl -X POST "http://localhost:8000/acl/login?username=researcher1&password=securepassword"
```

### 4. Use LDAP Authentication

Update `.mdjourney_acl.yaml`:

```yaml
identity_provider: ldap

# LDAP configuration via environment variables
# LDAP_SERVER=ldap://ldap.example.com:389
# LDAP_BASE_DN=dc=example,dc=com
# LDAP_USER_DN=uid={username},{base_dn}

users:
  - username: ldap_user1
    roles: [editor]
    # Password authentication handled by LDAP
```

## Advantages of ACL Approach

1. **No Database Required** - Uses YAML/JSON files
2. **Version Control Friendly** - ACL files can be versioned in Git
3. **External Integration** - Works with LDAP, OAuth, etc.
4. **Simple Deployment** - Just copy ACL file
5. **HPC Compatible** - Common in scientific computing environments
6. **Persistent API Keys** - Stored in configuration file
7. **Group Management** - Supports role-based groups

## Comparison: ACL vs Full User Accounts

| Feature | ACL-Based | Full User Accounts |
|---------|-----------|-------------------|
| Database Required | No | Yes |
| Password Storage | File or External | Database |
| User Registration | Admin-managed | Self-service |
| External Auth | Easy (LDAP/OAuth) | Requires integration |
| Deployment Complexity | Low | Medium |
| Scalability | Limited | High |
| Best For | Small teams, HPC | Large organizations |

## Security Considerations

1. **ACL File Permissions**: Restrict access to `.mdjourney_acl.yaml`
   ```bash
   chmod 600 .mdjourney_acl.yaml
   ```

2. **Password Hashing**: Use bcrypt (default) or stronger algorithms

3. **API Key Security**: Store API keys securely, rotate regularly

4. **LDAP**: Use TLS/SSL for LDAP connections

5. **Backup**: Regularly backup ACL configuration files

## Next Steps

- Add OAuth2/OIDC provider support
- Add password reset functionality
- Add user self-service profile updates
- Add audit logging for ACL changes
- Add ACL file validation and schema
