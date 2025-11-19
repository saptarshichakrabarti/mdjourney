from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import sqlite3

from .config import ALGORITHM, PUBLIC_KEY, DATABASE_URL
from .models import TokenData, User, UserInDB
import sqlite3

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_user(db: sqlite3.Connection, username: str):
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user:
        return UserInDB(**user)

def get_db():
    db = sqlite3.connect(DATABASE_URL, check_same_thread=False)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
