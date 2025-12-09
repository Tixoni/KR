import os
import time
import requests
import pytest


BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/")
AUTH_BASE = f"{BASE_URL}/api/auth"


def test_frontend_page_accessible():
    """Минимальный тест: frontend страница доступна."""
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200
        assert len(response.text) > 0
    except requests.RequestException:
        pytest.skip("Frontend not available")


def test_user_registration_flow():
    """Минимальный тест: регистрация пользователя через API."""
    unique_suffix = int(time.time())
    payload = {
        "username": f"frontend_e2e_{unique_suffix}",
        "password": "frontend_pass_123",
        "email": f"frontend_e2e_{unique_suffix}@example.com",
        "name": "Frontend E2E User",
        "phone": "+1234567890"
    }
    
    try:
        response = requests.post(f"{AUTH_BASE}/users", json=payload, timeout=10)
        # 201 при создании, 400 если уже существует
        assert response.status_code in (201, 400)
        if response.status_code == 201:
            user_data = response.json()
            assert user_data.get("username") == payload["username"]
    except requests.RequestException:
        pytest.skip("Auth service not available")


def test_user_login_logout_flow():
    """Минимальный тест: логин пользователя через API."""
    unique_suffix = int(time.time())
    username = f"frontend_login_{unique_suffix}"
    password = "login_pass_123"
    
    # Сначала регистрируем пользователя
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "name": "Login Test User",
        "phone": "+1234567890"
    }
    
    try:
        # Регистрация
        register_resp = requests.post(f"{AUTH_BASE}/users", json=register_payload, timeout=10)
        assert register_resp.status_code in (201, 400)
        
        # Логин
        login_resp = requests.post(f"{AUTH_BASE}/login", json={"username": username, "password": password}, timeout=10)
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data.get("token_type") == "bearer"
        
        # Проверяем доступ к защищенному эндпоинту
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_resp = requests.get(f"{AUTH_BASE}/users/me", headers=headers, timeout=10)
        assert me_resp.status_code == 200
        user_data = me_resp.json()
        assert user_data.get("username") == username
        
    except requests.RequestException:
        pytest.skip("Auth service not available")


def test_invalid_login_handling():
    """Минимальный тест: обработка неверных учетных данных."""
    try:
        response = requests.post(
            f"{AUTH_BASE}/login",
            json={"username": "nonexistent_user", "password": "wrong_password"},
            timeout=10
        )
        assert response.status_code == 401
    except requests.RequestException:
        pytest.skip("Auth service not available")

