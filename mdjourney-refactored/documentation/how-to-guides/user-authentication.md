# User Authentication and Account Management Guide

This guide explains how to implement user accounts and authentication in the MDJourney system.

## Current Authentication State

The system currently supports:
- **API Key Authentication**: Basic API key management via `APIKeyManager`
- **Role-Based Access Control (RBAC)**: Roles (admin, editor, viewer) with permission-based access
- **Gateway Session Management**: Session-based authentication through the gateway
- **Optional Authentication**: Can be enabled/disabled via `ENABLE_AUTHENTICATION` environment variable

**Limitations:**
- API keys are stored in-memory (not persistent)
- No user account database
- No password-based authentication
- No user registration/login endpoints
- No user profile management

**Alternative Approach:** See [RBAC-Based File-Based Authentication Guide](rbac-file-based-auth.md) for a lightweight approach that addresses these limitations using RBAC with file-based user storage, avoiding the need for a database.

## Implementation Strategy

### Phase 1: Database Setup for User Accounts

#### 1.1 Create User Model

Create `mdjourney-backend/models/user.py`:

```python
"""
User model for authentication and authorization.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    roles = Column(Text, default='["viewer"]')  # JSON array of roles
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    api_key = Column(String, unique=True, nullable=True, index=True)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        import json
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "roles": json.loads(self.roles) if isinstance(self.roles, str) else self.roles,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
```

#### 1.2 Database Initialization

Create `mdjourney-backend/app/db/database.py`:

```python
"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Database URL from environment or config
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./mdjourney_users.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from models.user import Base
    Base.metadata.create_all(bind=engine)
```

### Phase 2: User Registration and Login Endpoints

#### 2.1 Create User Service

Create `mdjourney-backend/app/services/user_service.py`:

```python
"""
User service for managing user accounts.
"""
import secrets
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from models.user import User
from app.db.database import get_db


class UserService:
    """Service for user account management."""

    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> User:
        """Create a new user account."""
        # Check if username or email already exists
        if self.db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=400, detail="Username already registered")

        if self.db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = User.get_password_hash(password)
        api_key = secrets.token_urlsafe(32)

        user = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            roles=json.dumps(roles or ["viewer"]),
            api_key=api_key,
            created_at=datetime.utcnow()
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = self.db.query(User).filter(User.username == username).first()

        if not user:
            return None

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is disabled")

        if not User.verify_password(password, user.hashed_password):
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()

        return user

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        return self.db.query(User).filter(User.api_key == api_key).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def update_user_roles(self, user_id: str, roles: List[str]) -> User:
        """Update user roles."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.roles = json.dumps(roles)
        self.db.commit()
        self.db.refresh(user)
        return user

    def regenerate_api_key(self, user_id: str) -> str:
        """Regenerate API key for a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_api_key = secrets.token_urlsafe(32)
        user.api_key = new_api_key
        self.db.commit()
        return new_api_key
```

#### 2.2 Create Authentication Router

Create `mdjourney-backend/routers/auth.py`:

```python
"""
Authentication endpoints for user registration and login.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.user_service import UserService
from app.core.auth import get_current_user, api_key_manager
from models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class UserRegister(BaseModel):
    """User registration request model."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    roles: list
    created_at: str
    api_key: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    api_key: str
    user: UserResponse


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user account."""
    user_service = UserService(db)

    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )

    user = user_service.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        roles=["viewer"]  # Default role
    )

    user_dict = user.to_dict()
    user_dict["api_key"] = user.api_key  # Include API key for new users
    return user_dict


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login and get API key."""
    user_service = UserService(db)

    user = user_service.authenticate_user(
        username=login_data.username,
        password=login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token (optional, for session management)
    from jose import jwt
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": user.username, "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    user_dict = user.to_dict()
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "api_key": user.api_key,
        "user": user_dict
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user_service = UserService(db)

    # Get user from API key
    api_key = current_user.get("api_key")
    if api_key:
        user = user_service.get_user_by_api_key(api_key)
        if user:
            return user.to_dict()

    # Fallback to current_user dict
    return current_user


@router.post("/regenerate-api-key")
async def regenerate_api_key(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate API key for current user."""
    user_service = UserService(db)

    # Get user ID from current_user
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    new_api_key = user_service.regenerate_api_key(user_id)
    return {"api_key": new_api_key}
```

### Phase 3: Update APIKeyManager to Use Database

Update `mdjourney-backend/app/core/auth.py`:

```python
# Update APIKeyManager to load from database
class APIKeyManager:
    """Manages API keys for authentication."""

    def __init__(self):
        self._api_keys: Dict[str, Dict] = {}
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from database."""
        try:
            from app.db.database import SessionLocal
            from models.user import User
            import json

            db = SessionLocal()
            try:
                users = db.query(User).filter(User.is_active == True).all()
                for user in users:
                    if user.api_key:
                        self._api_keys[user.api_key] = {
                            'id': user.id,
                            'name': user.username,
                            'email': user.email,
                            'roles': json.loads(user.roles) if isinstance(user.roles, str) else user.roles,
                            'created_at': user.created_at,
                            'last_used': user.last_login
                        }
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not load users from database: {e}")
            # Fallback to environment variable
            api_key = os.getenv('MDJOURNEY_API_KEY')
            if api_key:
                self._api_keys[api_key] = {
                    'name': 'default',
                    'roles': ['admin'],
                    'created_at': datetime.utcnow(),
                    'last_used': None
                }
```

### Phase 4: Update Frontend for User Authentication

#### 4.1 Update LoginPage Component

Update `mdjourney-webapp/src/pages/LoginPage.tsx`:

```typescript
import React, { useState } from 'react';
import {
  Button,
  Container,
  Typography,
  Box,
  Alert,
  TextField,
  Tabs,
  Tab,
  Paper
} from '@mui/material';
import apiClient from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface LoginForm {
  username: string;
  password: string;
}

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  fullName: string;
}

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [loginForm, setLoginForm] = useState<LoginForm>({ username: '', password: '' });
  const [registerForm, setRegisterForm] = useState<RegisterForm>({
    username: '',
    email: '',
    password: '',
    fullName: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError(null);
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/login', {
        username: loginForm.username,
        password: loginForm.password
      });

      // Store API key in localStorage
      localStorage.setItem('mdjourney_api_key', response.data.api_key);

      // Update axios default headers
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.api_key}`;

      login();
      navigate('/');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    setError(null);
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/register', {
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password,
        full_name: registerForm.fullName || undefined
      });

      // Auto-login after registration
      localStorage.setItem('mdjourney_api_key', response.data.api_key);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.api_key}`;

      login();
      navigate('/');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          MDJourney
        </Typography>
        <Typography variant="subtitle1" align="center" color="text.secondary">
          FAIR Metadata Management System
        </Typography>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
          <Tab label="Login" />
          <Tab label="Register" />
        </Tabs>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {tab === 0 ? (
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Username"
              value={loginForm.username}
              onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Password"
              type="password"
              value={loginForm.password}
              onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
              fullWidth
              required
            />
            <Button
              variant="contained"
              onClick={handleLogin}
              disabled={loading || !loginForm.username || !loginForm.password}
              fullWidth
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </Box>
        ) : (
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Username"
              value={registerForm.username}
              onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Email"
              type="email"
              value={registerForm.email}
              onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Full Name"
              value={registerForm.fullName}
              onChange={(e) => setRegisterForm({ ...registerForm, fullName: e.target.value })}
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={registerForm.password}
              onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
              fullWidth
              required
              helperText="Must be at least 8 characters"
            />
            <Button
              variant="contained"
              onClick={handleRegister}
              disabled={loading || !registerForm.username || !registerForm.email || !registerForm.password}
              fullWidth
            >
              {loading ? 'Registering...' : 'Register'}
            </Button>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default LoginPage;
```

#### 4.2 Update API Client

Update `mdjourney-webapp/src/services/api.ts` to include API key in requests:

```typescript
// Add API key to default headers
const apiKey = localStorage.getItem('mdjourney_api_key');
if (apiKey) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${apiKey}`;
}
```

### Phase 5: Update Dependencies

Add required packages to `pyproject.toml`:

```toml
[project.optional-dependencies]
api = [
    # ... existing dependencies ...
    "sqlalchemy>=2.0.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.6",  # For form data
    "email-validator>=2.0.0",  # For EmailStr validation
]
```

### Phase 6: Database Migration Script

Create `mdjourney-backend/scripts/init_users_db.py`:

```python
#!/usr/bin/env python3
"""Initialize user database."""
from app.db.database import init_db

if __name__ == "__main__":
    print("Initializing user database...")
    init_db()
    print("Database initialized successfully!")
```

### Phase 7: Configuration Updates

Update `env.example`:

```bash
# Authentication
ENABLE_AUTHENTICATION=true
DATABASE_URL=sqlite:///./mdjourney_users.db
JWT_SECRET_KEY=your-secret-key-change-in-production

# For PostgreSQL (production):
# DATABASE_URL=postgresql://user:password@localhost/mdjourney
```

## Usage

### 1. Initialize Database

```bash
cd mdjourney-backend
python scripts/init_users_db.py
```

### 2. Enable Authentication

Set environment variable:
```bash
export ENABLE_AUTHENTICATION=true
```

Or in `.fair_meta_config.yaml`:
```yaml
security:
  authentication:
    enabled: true
```

### 3. Register First User

Use the frontend registration form or API:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword123",
    "full_name": "Administrator"
  }'
```

### 4. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "securepassword123"
  }'
```

Response includes `api_key` which should be used for subsequent requests.

## Security Considerations

1. **Password Hashing**: Uses bcrypt via passlib
2. **API Keys**: Cryptographically secure random tokens
3. **SQL Injection**: Protected by SQLAlchemy ORM
4. **Rate Limiting**: Already implemented in security middleware
5. **HTTPS**: Required in production
6. **JWT Tokens**: Optional, can be used for session management

## Next Steps

- Add password reset functionality
- Add email verification
- Add user profile management endpoints
- Add admin user management interface
- Add audit logging for user actions
- Add two-factor authentication (2FA)
