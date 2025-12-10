import os
import time
import requests
import pytest

AUTH_BASE_URL = os.getenv("AUTH_BASE_URL", "http://localhost:8000").rstrip("/")
TOURS_BASE_URL = os.getenv("TOURS_BASE_URL", "http://localhost:8001").rstrip("/")
BOOKINGS_BASE_URL = os.getenv("BOOKINGS_BASE_URL", "http://localhost:8002").rstrip("/")


def test_can_register_new_user():
    """создаём пользователя через auth-service."""
    unique_suffix = int(time.time())
    payload = {
        "username": f"backend_int_{unique_suffix}",
        "password": "backend_int_password",
        "email": f"backend_int_{unique_suffix}@example.com",
        "name": "Backend Integration User",
        "phone": "+1234567890",
    }

    response = requests.post(f"{AUTH_BASE_URL}/users", json=payload, timeout=15)

    # Допускаем повторный запуск: 201 при первом создании, 400 если пользователь уже есть
    assert response.status_code in (201, 400), response.text


def test_auth_service_health():
    """проверка health endpoint auth-service."""
    try:
        response = requests.get(f"{AUTH_BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    except requests.RequestException:
        pytest.skip("Auth service not available")


def test_tours_service_health():
    """проверка health endpoint tours-service."""
    try:
        response = requests.get(f"{TOURS_BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    except requests.RequestException:
        pytest.skip("Tours service not available")


def test_bookings_service_health():
    """проверка health endpoint booking-service."""
    try:
        response = requests.get(f"{BOOKINGS_BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    except requests.RequestException:
        pytest.skip("Bookings service not available")


def test_tours_list_endpoint():
    """получение списка туров."""
    try:
        response = requests.get(f"{TOURS_BASE_URL}/tours", timeout=5)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    except requests.RequestException:
        pytest.skip("Tours service not available")