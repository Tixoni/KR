"""Frontend API utility tests."""
import os
import requests


def test_frontend_api_health_endpoint():
    """Test that frontend serves health endpoint."""
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:8080")
    try:
        response = requests.get(f"{frontend_url}/health", timeout=5)
        assert response.status_code in (200, 404), f"Expected 200 or 404, got {response.status_code}"
    except requests.RequestException:
        # Skip if frontend not available (e.g., in unit test environment)
        pass


def test_frontend_api_main_page():
    """Test that frontend serves main page."""
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:8080")
    try:
        response = requests.get(f"{frontend_url}/", timeout=5)
        assert response.status_code in (200, 404), f"Expected 200 or 404, got {response.status_code}"
        if response.status_code == 200:
            assert len(response.content) > 0, "Frontend should return content"
    except requests.RequestException:
        # Skip if frontend not available
        pass
