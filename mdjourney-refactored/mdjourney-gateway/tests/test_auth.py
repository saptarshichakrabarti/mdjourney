import pytest
from fastapi.testclient import TestClient
from main import app
import sqlite3
import os

from auth.auth import get_password_hash

client = TestClient(app)

DATABASE_URL = "test.db"

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    # Create a test database
    db = sqlite3.connect(DATABASE_URL)
    with open("../../auth/migrations/001_init.sql", "r") as f:
        db.executescript(f.read())
    db.commit()
    db.close()

    # Monkeypatch the DATABASE_URL in the config module
    from auth import config
    config.DATABASE_URL = DATABASE_URL
    yield

    # Teardown the database
    os.remove(DATABASE_URL)

def test_login_for_access_token(cleanup_user):
    client.post("/users/", json={"username": "testuser", "password": "test"})
    response = client.post("/auth/token", data={"username": "testuser", "password": "test"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_for_access_token_incorrect_password(cleanup_user):
    client.post("/users/", json={"username": "testuser", "password": "test"})
    response = client.post("/auth/token", data={"username": "testuser", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_incorrect_username(cleanup_user):
    response = client.post("/auth/token", data={"username": "wronguser", "password": "test"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

@pytest.fixture
def cleanup_user():
    yield
    client.delete("/users/anotheruser")
    client.delete("/users/testuser")

def test_create_user(cleanup_user):
    response = client.post("/users/", json={"username": "anotheruser", "password": "password"})
    print(f"test_create_user: {response.json()}")
    assert response.status_code == 200
    assert response.json()["username"] == "anotheruser"

def test_create_duplicate_user(cleanup_user):
    client.post("/users/", json={"username": "testuser", "password": "password"})
    response = client.post("/users/", json={"username": "testuser", "password": "password"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

def test_protected_endpoint_unauthenticated():
    response = client.get("/api/health")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
