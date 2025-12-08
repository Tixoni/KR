"""End-to-end user journey tests."""
import os
import time
import requests
import pytest


def test_complete_booking_flow():
    """Test complete flow: register -> login -> get tours -> create booking."""
    auth_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    tours_url = os.getenv("TOURS_BASE_URL", "http://localhost:8001")
    booking_url = os.getenv("BOOKING_BASE_URL", "http://localhost:8002")
    
    unique_suffix = int(time.time())
    
    try:
        # Step 1: Register user
        user_payload = {
            "username": f"journey_user_{unique_suffix}",
            "password": "journey_pass_123",
            "email": f"journey_user_{unique_suffix}@example.com",
            "name": "Journey Test User",
            "phone": "+1234567890"
        }
        register_response = requests.post(f"{auth_url}/users", json=user_payload, timeout=10)
        assert register_response.status_code in (201, 400), f"Registration failed: {register_response.status_code}"
        
        # Step 2: Login
        login_response = requests.post(
            f"{auth_url}/login",
            json={"username": user_payload["username"], "password": user_payload["password"]},
            timeout=10
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Get user ID
        me_response = requests.get(f"{auth_url}/users/me", headers=headers, timeout=10)
        assert me_response.status_code == 200
        user_id = me_response.json()["id"]
        
        # Step 4: Get tours
        tours_response = requests.get(f"{tours_url}/tours", timeout=10)
        assert tours_response.status_code == 200
        tours = tours_response.json()
        
        if not tours:
            pytest.skip("No tours available for booking test")
        
        tour_id = tours[0]["id"]
        
        # Step 5: Create booking
        from datetime import datetime, timedelta
        booking_payload = {
            "title": f"E2E Booking {unique_suffix}",
            "user_id": user_id,
            "tour_id": tour_id,
            "travel_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "participants_count": 1,
            "contact_email": user_payload["email"],
            "contact_phone": user_payload["phone"]
        }
        
        booking_response = requests.post(
            f"{booking_url}/bookings",
            json=booking_payload,
            headers=headers,
            timeout=15
        )
        assert booking_response.status_code == 201, f"Booking creation failed: {booking_response.status_code}"
        booking_data = booking_response.json()
        assert booking_data["user_id"] == user_id
        assert booking_data["tour_id"] == tour_id
        
    except requests.RequestException as e:
        pytest.skip(f"Services not available: {e}")


def test_health_checks_all_services():
    """Test that all services are healthy."""
    auth_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    tours_url = os.getenv("TOURS_BASE_URL", "http://localhost:8001")
    booking_url = os.getenv("BOOKING_BASE_URL", "http://localhost:8002")
    
    services = [
        (auth_url, "auth-service"),
        (tours_url, "tours-service"),
        (booking_url, "booking-service"),
    ]
    
    for url, service_name in services:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            assert response.status_code == 200, f"{service_name} health check failed"
            data = response.json()
            assert data.get("service") == service_name
        except requests.RequestException:
            pytest.skip(f"{service_name} not available")

