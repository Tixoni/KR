"""Performance tests for API response times."""
import os
import time
import requests
import pytest


def test_api_response_time_acceptable():
    """Test that API endpoints respond within acceptable time."""
    auth_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    tours_url = os.getenv("TOURS_BASE_URL", "http://localhost:8001")
    booking_url = os.getenv("BOOKING_BASE_URL", "http://localhost:8002")
    
    max_response_time = 2.0  # seconds
    
    endpoints = [
        (auth_url, "/health"),
        (tours_url, "/health"),
        (booking_url, "/health"),
    ]
    
    for base_url, path in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{path}", timeout=5)
            elapsed_time = time.time() - start_time
            
            assert response.status_code == 200, f"{base_url}{path} returned {response.status_code}"
            assert elapsed_time < max_response_time, f"{base_url}{path} took {elapsed_time:.2f}s (max: {max_response_time}s)"
        except requests.RequestException:
            pytest.skip(f"Service {base_url} not available")


def test_tours_list_response_time():
    """Test that tours list endpoint responds quickly."""
    tours_url = os.getenv("TOURS_BASE_URL", "http://localhost:8001")
    max_response_time = 1.0  # seconds
    
    try:
        start_time = time.time()
        response = requests.get(f"{tours_url}/tours", timeout=5)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < max_response_time, f"Tours list took {elapsed_time:.2f}s (max: {max_response_time}s)"
    except requests.RequestException:
        pytest.skip("Tours service not available")

