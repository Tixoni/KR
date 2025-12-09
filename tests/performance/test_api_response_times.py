"""Минимальные тесты производительности API."""
import os
import time
import requests
import pytest


BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/")
GATEWAY_HEALTH = f"{BASE_URL}/health"
AUTH_BASE = f"{BASE_URL}/api/auth"
TOURS_BASE = f"{BASE_URL}/api/tours"


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
    """Пропустить тест, если gateway недоступен."""
    if not wait_for_gateway_ready(timeout_seconds=30):
        pytest.skip(f"Gateway at {GATEWAY_HEALTH} not reachable")


def test_health_endpoint_response_time():
    """Минимальный тест: health endpoint отвечает быстро."""
    require_gateway_or_skip()
    
    try:
        start_time = time.time()
        response = requests.get(GATEWAY_HEALTH, timeout=5)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Health endpoint returned {response.status_code}"
        # Health endpoint должен отвечать быстро (менее 1 секунды)
        assert elapsed_time < 1.0, f"Health endpoint too slow: {elapsed_time:.2f}s"
    except requests.RequestException as e:
        pytest.skip(f"Gateway not available: {e}")


def test_auth_health_response_time():
    """Минимальный тест: auth health endpoint отвечает быстро."""
    require_gateway_or_skip()
    
    try:
        start_time = time.time()
        response = requests.get(f"{AUTH_BASE}/health", timeout=5)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Auth health returned {response.status_code}"
        # Health endpoint должен отвечать быстро (менее 2 секунд)
        assert elapsed_time < 2.0, f"Auth health endpoint too slow: {elapsed_time:.2f}s"
    except requests.RequestException as e:
        pytest.skip(f"Auth service not available: {e}")


def test_tours_list_response_time():
    """Минимальный тест: список туров загружается за разумное время."""
    require_gateway_or_skip()
    
    try:
        start_time = time.time()
        response = requests.get(f"{TOURS_BASE}/tours", timeout=10)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Tours endpoint returned {response.status_code}"
        # Список туров должен загружаться за разумное время (менее 5 секунд)
        assert elapsed_time < 5.0, f"Tours list endpoint too slow: {elapsed_time:.2f}s"
    except requests.RequestException as e:
        pytest.skip(f"Tours service not available: {e}")

