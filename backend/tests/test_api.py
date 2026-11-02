"""
Backend integration tests.

Run against the live Uvicorn server using synchronous `requests`.
All tests require the backend to be running with Atlas connected.
"""
import os
import uuid
from io import BytesIO

import pytest
import requests
from PIL import Image

BASE = os.environ.get("SMARTAGRI_API_BASE_URL", "http://localhost:8000")


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _post(path, json=None, data=None, files=None, headers=None, timeout=30):
    return requests.post(f"{BASE}{path}", json=json, data=data, files=files,
                         headers=headers, timeout=timeout)

def _get(path, headers=None, params=None, timeout=30):
    return requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=timeout)

def _put(path, json=None, headers=None, timeout=30):
    return requests.put(f"{BASE}{path}", json=json, headers=headers, timeout=timeout)

def _delete(path, headers=None, timeout=30):
    return requests.delete(f"{BASE}{path}", headers=headers, timeout=timeout)


# â”€â”€ Health â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_health_check(client):
    r = _get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "healthy"
    assert d["database_connected"] is True
    assert d["database"] in ("atlas", "local")


def test_root_endpoint(client):
    r = _get("/")
    assert r.status_code == 200
    assert "name" in r.json()


def test_swagger_docs(client):
    r = _get("/docs")
    assert r.status_code == 200


# â”€â”€ Authentication â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_register_user(client):
    uid = uuid.uuid4().hex[:8]
    r = _post("/api/auth/register", json={
        "full_name": "New User",
        "email": f"new_{uid}@test.com",
        "mobile_number": "9876543210",
        "password": "pass123456",
        "confirm_password": "pass123456",
    })
    assert r.status_code == 201, r.text
    d = r.json()
    assert "access_token" in d
    assert d["full_name"] == "New User"
    assert d["role"] == "user"


def test_register_duplicate_email(client, auth_token):
    # Get the email from /me
    me = _get("/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"}).json()
    r = _post("/api/auth/register", json={
        "full_name": "Dup", "email": me["email"],
        "mobile_number": "0000000000",
        "password": "pass123456", "confirm_password": "pass123456",
    })
    assert r.status_code == 409


def test_register_password_mismatch(client):
    uid = uuid.uuid4().hex[:8]
    r = _post("/api/auth/register", json={
        "full_name": "Mismatch", "email": f"mismatch_{uid}@test.com",
        "mobile_number": "1234567890",
        "password": "pass123456", "confirm_password": "different456",
    })
    assert r.status_code == 422


def test_login_success(client, auth_token):
    """Auth token fixture proves login works; also test directly."""
    me = _get("/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"}).json()
    # Re-login with known-good admin
    r = _post("/api/auth/login", json={
        "email": "admin@smartagri.com", "password": "admin123456"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_invalid_credentials(client):
    r = _post("/api/auth/login", json={
        "email": "nobody@test.com", "password": "wrongpass"
    })
    assert r.status_code == 401


def test_get_me(client, auth_headers):
    r = _get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert "full_name" in d
    assert "email" in d


def test_protected_route_without_token(client):
    r = _get("/api/auth/me")
    assert r.status_code == 401


def test_forgot_password(client, auth_token):
    me = _get("/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"}).json()
    r = _post("/api/auth/forgot-password", json={"email": me["email"]})
    assert r.status_code == 200
    assert "message" in r.json()


def test_forgot_password_nonexistent_email(client):
    r = _post("/api/auth/forgot-password", json={"email": "nobody_xyz@test.com"})
    assert r.status_code == 200  # always 200 to avoid email enumeration


# â”€â”€ Crop recommendation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_crop_recommendation(client, auth_headers):
    r = _post("/api/crop/recommend", json={
        "nitrogen": 80, "phosphorus": 45, "potassium": 40,
        "temperature": 25, "humidity": 70, "ph": 6.5,
        "rainfall": 120, "soil_type": "Loamy", "location": "Punjab",
    }, headers=auth_headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "recommendations" in d
    assert len(d["recommendations"]) > 0
    assert "top_recommendation" in d
    assert "soil_info" in d


def test_crop_recommendation_validation(client, auth_headers):
    """N > 200 should fail validation."""
    r = _post("/api/crop/recommend", json={
        "nitrogen": 999, "phosphorus": 45, "potassium": 40,
        "temperature": 25, "humidity": 70, "ph": 6.5,
        "rainfall": 120, "soil_type": "Loamy", "location": "",
    }, headers=auth_headers)
    assert r.status_code == 422


# â”€â”€ Yield prediction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_yield_prediction(client, auth_headers):
    r = _post("/api/yield/predict", json={
        "crop_type": "Rice", "state": "Punjab", "season": "Kharif",
        "area": 2.0, "rainfall": 1000, "temperature": 28,
        "soil_type": "Loamy", "fertilizer_usage": 100,
    }, headers=auth_headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "predicted_yield" in d
    assert d["predicted_yield"] > 0
    assert d["is_estimate"] is True


def test_yield_options(client, auth_headers):
    r = _get("/api/yield/options", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert "crops" in d
    assert "seasons" in d
    assert "states" in d


# â”€â”€ Disease detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_disease_prediction(client, auth_headers):
    """Test disease detection with a synthetic leaf image."""
    import numpy as np
    img = Image.fromarray(
        (np.array([[[40, 120, 30]] * 256] * 256, dtype="uint8"))
    )
    buf = BytesIO()
    img.save(buf, "JPEG")
    buf.seek(0)

    r = _post("/api/disease/predict",
              data={"crop_type": "Tomato"},
              files={"file": ("leaf.jpg", buf, "image/jpeg")},
              headers=auth_headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "disease_name" in d
    assert "confidence" in d
    assert "is_healthy" in d
    assert "is_demo_mode" in d
    # The CNN classifies the leaf — crop_type in response is the CNN's prediction, not the hint
    assert isinstance(d["crop_type"], str) and len(d["crop_type"]) > 0


def test_disease_invalid_file(client, auth_headers):
    """Non-image file should be rejected."""
    r = _post("/api/disease/predict",
              data={"crop_type": "Tomato"},
              files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
              headers=auth_headers)
    assert r.status_code == 400


def test_disease_model_info(client, auth_headers):
    r = _get("/api/disease/model-info", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] in ("production", "demo")
    assert "model_loaded" in d


# â”€â”€ History â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_disease_history(client, auth_headers):
    r = _get("/api/disease/history", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert "items" in d
    assert "total" in d


def test_crop_history(client, auth_headers):
    r = _get("/api/crop/history", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()


def test_yield_history(client, auth_headers):
    r = _get("/api/yield/history", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()


# â”€â”€ User profile â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_user_profile_update(client, auth_headers):
    r = _put("/api/users/profile", json={
        "full_name": "Updated Name",
        "farm_name": "Test Farm",
        "location": "Test State, India",
    }, headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["full_name"] == "Updated Name"
    assert d["farm_name"] == "Test Farm"


# â”€â”€ Weather â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_weather_forecast(client, auth_headers):
    r = _get("/api/weather/forecast", headers=auth_headers,
             params={"lat": 28.6139, "lon": 77.209, "location": "New Delhi"})
    assert r.status_code == 200
    d = r.json()
    assert "current" in d
    assert "forecast" in d
    assert "farming_advice" in d


# â”€â”€ Supported crops â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_supported_crops(client):
    r = _get("/api/disease/crops")
    assert r.status_code == 200
    d = r.json()
    assert "crops" in d
    assert len(d["crops"]) >= 8


# â”€â”€ Admin â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_admin_dashboard_requires_admin(client, auth_headers):
    """Regular user must get 403 on admin endpoints."""
    r = _get("/api/admin/dashboard", headers=auth_headers)
    assert r.status_code == 403


def test_admin_dashboard(client):
    """Admin login and dashboard access."""
    login = _post("/api/auth/login",
                  json={"email": "admin@smartagri.com", "password": "admin123456"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    r = _get("/api/admin/dashboard",
             headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    d = r.json()
    assert "stats" in d
    assert "total_users" in d["stats"]


def test_live_weather_falls_back_when_owm_unavailable(client, auth_headers):
    """Live weather remains available if OpenWeatherMap is unconfigured or rejects its key."""
    r = _get("/api/crop/live-weather", headers=auth_headers,
             params={"lat": 28.6, "lon": 77.2})
    assert r.status_code == 200, r.text
    data = r.json()
    assert {"temperature", "humidity", "rainfall", "description", "city", "source"} <= data.keys()
    assert data["source"] in ("openweathermap", "open-meteo")
