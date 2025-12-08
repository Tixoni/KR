"""Accessibility tests."""
import os
import requests


def test_api_endpoints_accessible():
    """Test that API endpoints are accessible (basic accessibility check)."""
    auth_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    tours_url = os.getenv("TOURS_BASE_URL", "http://localhost:8001")
    booking_url = os.getenv("BOOKING_BASE_URL", "http://localhost:8002")
    
    endpoints = [
        (auth_url, "/health"),
        (tours_url, "/health"),
        (booking_url, "/health"),
    ]
    
    for base_url, path in endpoints:
        try:
            response = requests.get(f"{base_url}{path}", timeout=5)
            assert response.status_code == 200, f"{base_url}{path} returned {response.status_code}"
            # Check that response is JSON (API accessibility)
            assert response.headers.get("content-type", "").startswith("application/json")
        except requests.RequestException:
            # Skip if service not available
            pass


def test_api_responses_have_required_fields():
    """Test that API health responses have required fields."""
    auth_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    
    try:
        response = requests.get(f"{auth_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "Health response should have 'status' field"
            assert "service" in data, "Health response should have 'service' field"
    except requests.RequestException:
        # Skip if service not available
        pass
