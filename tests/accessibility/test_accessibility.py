import os
import time
import requests
import pytest


BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/")
GATEWAY_HEALTH = f"{BASE_URL}/health"


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


def test_frontend_page_loads():
    require_gateway_or_skip()
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200, f"Frontend returned {response.status_code}"
        assert "Tourism Platform" in response.text or "tourism" in response.text.lower()
    except requests.RequestException as e:
        pytest.skip(f"Frontend not available: {e}")


def test_html_structure_basic():
    require_gateway_or_skip()
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200, f"Frontend returned {response.status_code}"
        html = response.text.lower()
        # Проверяем наличие основных элементов
        assert "<html" in html or "<!doctype" in html
        assert "<head" in html
        assert "<body" in html
    except requests.RequestException as e:
        pytest.skip(f"Frontend not available: {e}")


def test_css_loads():
    require_gateway_or_skip()
    
    try:
        response = requests.get(f"{BASE_URL}/styles.css", timeout=5)
        # CSS может быть 200 или 404, но не должно быть 500
        assert response.status_code != 500, f"CSS endpoint returned {response.status_code}"
    except requests.RequestException as e:
        pytest.skip(f"Frontend not available: {e}")

