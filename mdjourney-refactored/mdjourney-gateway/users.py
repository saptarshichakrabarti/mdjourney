from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from auth.auth import get_password_hash, get_db
from auth.models import User, UserCreate

router = APIRouter()

@router.post("/", response_model=User)
def create_user(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    try:
        db.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (user.username, hashed_password),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already registered")
    return user

@router.delete("/{username}")
def delete_user(username: str, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM users WHERE username = ?", (username,))
    db.commit()
    return {"message": "User deleted"}
