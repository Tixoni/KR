import os
import time
import requests
import pytest


BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/")
GATEWAY_HEALTH = f"{BASE_URL}/health"
AUTH_BASE = f"{BASE_URL}/api/auth"


def wait_for_gateway_ready(timeout_seconds: int = 60) -> bool:
    """Return True if gateway becomes ready within timeout, else False."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            resp = requests.get(GATEWAY_HEALTH, timeout=3)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    return False


def require_gateway_or_skip():
    if not wait_for_gateway_ready(timeout_seconds=30):
        pytest.skip(f"Gateway at {GATEWAY_HEALTH} not reachable")


def test_frontend_page_accessible():
    """frontend страница доступна."""
    require_gateway_or_skip()
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200, f"Frontend returned {response.status_code}"
        assert len(response.text) > 0
    except requests.RequestException as e:
        pytest.skip(f"Frontend not available: {e}")


def test_user_registration_flow():
    """регистрация пользователя через API."""
    require_gateway_or_skip()
    
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
        assert response.status_code in (201, 400), f"Registration returned {response.status_code} - {response.text}"
        if response.status_code == 201:
            user_data = response.json()
            assert user_data.get("username") == payload["username"]
    except requests.RequestException as e:
        pytest.skip(f"Auth service not available: {e}")


def test_user_login_logout_flow():
    """логин пользователя через API."""
    require_gateway_or_skip()
    
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
        assert register_resp.status_code in (201, 400), f"Registration returned {register_resp.status_code}"
        
        # Логин
        login_resp = requests.post(f"{AUTH_BASE}/login", json={"username": username, "password": password}, timeout=10)
        assert login_resp.status_code == 200, f"Login returned {login_resp.status_code} - {login_resp.text}"
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data.get("token_type") == "bearer"
        
        # Проверяем доступ к защищенному эндпоинту
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_resp = requests.get(f"{AUTH_BASE}/users/me", headers=headers, timeout=10)
        assert me_resp.status_code == 200, f"Users/me returned {me_resp.status_code}"
        user_data = me_resp.json()
        assert user_data.get("username") == username
        
    except requests.RequestException as e:
        pytest.skip(f"Auth service not available: {e}")


def test_invalid_login_handling():
    """обработка неверных учетных данных."""
    require_gateway_or_skip()
    
    try:
        response = requests.post(
            f"{AUTH_BASE}/login",
            json={"username": "nonexistent_user", "password": "wrong_password"},
            timeout=10
        )
        assert response.status_code == 401, f"Expected 401 for invalid login, got {response.status_code}"
    except requests.RequestException as e:
        pytest.skip(f"Auth service not available: {e}")

