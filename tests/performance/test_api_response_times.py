"""Минимальные тесты производительности API."""
import os
import time
import requests
import pytest


BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/")
AUTH_BASE = f"{BASE_URL}/api/auth"
TOURS_BASE = f"{BASE_URL}/api/tours"


def test_health_endpoint_response_time():
    """Минимальный тест: health endpoint отвечает быстро."""
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        # Health endpoint должен отвечать быстро (менее 1 секунды)
        assert elapsed_time < 1.0, f"Health endpoint too slow: {elapsed_time:.2f}s"
    except requests.RequestException:
        pytest.skip("Gateway not available")


def test_auth_health_response_time():
    """Минимальный тест: auth health endpoint отвечает быстро."""
    try:
        start_time = time.time()
        response = requests.get(f"{AUTH_BASE}/health", timeout=5)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        # Health endpoint должен отвечать быстро (менее 2 секунд)
        assert elapsed_time < 2.0, f"Auth health endpoint too slow: {elapsed_time:.2f}s"
    except requests.RequestException:
        pytest.skip("Auth service not available")


def test_tours_list_response_time():
    """Минимальный тест: список туров загружается за разумное время."""
    try:
        start_time = time.time()
        response = requests.get(f"{TOURS_BASE}/tours", timeout=10)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        # Список туров должен загружаться за разумное время (менее 5 секунд)
        assert elapsed_time < 5.0, f"Tours list endpoint too slow: {elapsed_time:.2f}s"
    except requests.RequestException:
        pytest.skip("Tours service not available")

