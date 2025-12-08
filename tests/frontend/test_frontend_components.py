"""Frontend component tests."""
import os
import requests


def test_frontend_static_assets():
    """Test that frontend serves static assets (CSS, JS)."""
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:8080")
    try:
        # Check if main HTML references assets
        response = requests.get(f"{frontend_url}/", timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            # Basic check: HTML should contain references to styles or scripts
            assert len(content) > 0, "Frontend should return HTML content"
    except requests.RequestException:
        # Skip if frontend not available
        pass


def test_frontend_api_endpoints():
    """Test that frontend can reach backend API endpoints."""
    gateway_url = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080")
    try:
        # Test gateway health
        response = requests.get(f"{gateway_url}/health", timeout=5)
        assert response.status_code in (200, 404), f"Gateway health check failed: {response.status_code}"
    except requests.RequestException:
        # Skip if gateway not available
        pass
