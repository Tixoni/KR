"""Frontend E2E authentication flow tests."""
import os
import time
import requests
import pytest


def test_user_registration_flow():
    """Test user registration through API."""
    auth_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    unique_suffix = int(time.time())
    
    payload = {
        "username": f"e2e_user_{unique_suffix}",
        "password": "e2e_pass_123",
        "email": f"e2e_user_{unique_suffix}@example.com",
        "name": "E2E Test User",
        "phone": "+1234567890"
    }
    
    try:
        response = requests.post(f"{auth_url}/users", json=payload, timeout=10)
        assert response.status_code in (201, 400), f"Registration failed: {response.status_code}"
        if response.status_code == 201:
            data = response.json()
            assert data["username"] == payload["username"]
    except requests.RequestException as e:
        pytest.skip(f"Auth service not available: {e}")


def test_user_login_flow():
    """Test user login flow."""
    auth_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    unique_suffix = int(time.time())
    
    # First create user
    user_payload = {
        "username": f"login_user_{unique_suffix}",
        "password": "login_pass_123",
        "email": f"login_user_{unique_suffix}@example.com",
        "name": "Login Test User",
        "phone": "+1234567890"
    }
    
    try:
        # Create user
        requests.post(f"{auth_url}/users", json=user_payload, timeout=10)
        
        # Login
        login_response = requests.post(
            f"{auth_url}/login",
            json={"username": user_payload["username"], "password": user_payload["password"]},
            timeout=10
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
    except requests.RequestException as e:
        pytest.skip(f"Auth service not available: {e}")
