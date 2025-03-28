import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from native_authentication.main import app
from native_authentication.db.base import Base, get_db
from native_authentication.models.user import User
from native_authentication.core.security import create_access_token, get_password_hash

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create the tables before each test run
def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create a test user
    db = TestingSessionLocal()
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    yield db

    # Clean up
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_register_user(test_db):
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data


def get_tokens(test_db):
    """Helper function to get tokens."""
    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "password123"}
    )
    data = response.json()
    return data["access_token"], data["refresh_token"]


def test_login_user(test_db):
    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    access_token = data["access_token"]

    # Test accessing protected endpoint with the token
    response = client.get("/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200


def test_refresh_token(test_db):
    """Test refreshing access token."""
    # First login to get tokens
    access_token, refresh_token = get_tokens(test_db)

    # Use refresh token to get a new access token
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test the new access token
    new_access_token = data["access_token"]
    response = client.get("/", headers={"Authorization": f"Bearer {new_access_token}"})
    assert response.status_code == 200


def test_logout(test_db):
    # First login to get tokens
    access_token, _ = get_tokens(test_db)

    # Logout
    response = client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"

    # Try to use the token again (should fail)
    response = client.get("/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401


def test_example_workflow(test_db):
    """
    An example workflow demonstrating how to use this authentication system in a real application.

    This test demonstrates:
    1. User registration
    2. User login
    3. Using the access token to access protected resources
    4. Refreshing the access token
    5. Logging out
    """
    print("1. Registering a new user...")
    register_response = client.post(
        "/auth/register",
        json={
            "username": "example_user",
            "email": "example@example.com",
            "password": "securepassword123",
            "full_name": "Example User",
        },
    )
    assert register_response.status_code == 200
    user_data = register_response.json()
    print(f"User registered with ID: {user_data['id']}")

    print("\n2. Logging in with the new user...")
    login_response = client.post(
        "/auth/login",
        data={"username": "example_user", "password": "securepassword123"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print("Login successful, received access and refresh tokens")

    print("\n3. Accessing protected endpoints...")
    protected_response = client.get(
        "/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert protected_response.status_code == 200
    print("Successfully accessed protected endpoint with access token")

    print("\n4. Refreshing the access token...")
    refresh_response = client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    new_access_token = new_tokens["access_token"]
    print("Successfully refreshed access token")

    print("\n5. Using the new access token...")
    new_protected_response = client.get(
        "/", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert new_protected_response.status_code == 200
    print("Successfully accessed protected endpoint with new access token")

    print("\n6. Logging out...")
    logout_response = client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert logout_response.status_code == 200
    print("Successfully logged out, token has been invalidated")

    print("\n7. Trying to use the invalidated token...")
    invalid_response = client.get(
        "/", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert invalid_response.status_code == 401
    print("As expected, the token is now invalid")


if __name__ == "__main__":
    try:
        setup_module(None)
        with TestingSessionLocal() as db:
            test_db_instance = db
            test_example_workflow(test_db_instance)
        print("\nExample workflow completed successfully!")
    finally:
        Base.metadata.drop_all(bind=engine)
