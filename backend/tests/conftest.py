"""Pytest configuration and fixtures for integration tests.

Tests run against the LIVE Uvicorn server at http://localhost:8000 using
the synchronous 'requests' library.

Rationale:
  Python 3.14 has async library compatibility issues with both motor (SSL
  in worker threads) and httpx/anyio (read timeout with anyio backend).
  Synchronous requests against the already-running Uvicorn process avoids
  all of these and still provides full integration coverage against the
  live Atlas cluster.

  Start the backend before running tests:
    cd backend
    .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import uuid
import pytest
import requests

BASE = "http://localhost:8000"


@pytest.fixture(scope="session")
def live_server():
    """Verify the live server is reachable before running any test."""
    try:
        r = requests.get(f"{BASE}/health", timeout=10)
        r.raise_for_status()
        data = r.json()
        assert data["status"] == "healthy", f"Server not healthy: {data}"
        assert data.get("database_connected"), "Database not connected"
        print(f"\n  Live server OK — database: {data.get('database')}")
    except Exception as exc:
        pytest.skip(f"Live server not reachable at {BASE}: {exc}")
    return BASE


@pytest.fixture
def client(live_server):
    """Return the base URL of the live server."""
    return live_server


@pytest.fixture
def auth_token(client):
    """Register a unique test user and return a fresh JWT access token."""
    unique = uuid.uuid4().hex[:8]
    resp = requests.post(f"{client}/api/auth/register", json={
        "full_name": "Test User",
        "email": f"test_{unique}@test.com",
        "mobile_number": "1234567890",
        "password": "test123456",
        "confirm_password": "test123456",
    }, timeout=30)
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Return Authorization headers for a freshly registered test user."""
    return {"Authorization": f"Bearer {auth_token}"}
