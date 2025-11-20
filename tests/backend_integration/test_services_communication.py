import pytest
import requests
import time
import os
import subprocess
from datetime import datetime, timedelta

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8080/api")
AUTH_URL = f"{BASE_URL}/auth"
TOURS_URL = f"{BASE_URL}/tours" 
BOOKINGS_URL = f"{BASE_URL}/bookings"

TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "password": "testpass123",
    "email": f"test{int(time.time())}@example.com",
    "name": "Test User",
    "phone": "+1234567890"
}

TEST_TOUR = {
    "title": "Test Tour Paris",
    "destination": "Paris", 
    "price": 50000.0,
    "duration_days": 7,
    "description": "Paris excursion tour",
    "features": ["Excursions", "Transfer", "Breakfasts"],
    "available": True
}

def wait_for_service(url: str, timeout: int = 120):
    print(f"Waiting for {url}")
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < timeout:
        attempt += 1
        try:
            response = requests.get(url, timeout=10)
            print(f"Attempt {attempt}: {url} -> {response.status_code}")
            
            if response.status_code == 200:
                print(f"Service {url} is available")
                return True
                
        except requests.ConnectionError as e:
            print(f"Connection error to {url}: {e}")
        except requests.Timeout:
            print(f"Timeout connecting to {url}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            
        time.sleep(5)
    
    print(f"Service {url} not available after {timeout} seconds")
    return False

def get_auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="session")
def services_ready():
    print("Checking service readiness...")
    
    services = [
        f"{AUTH_URL}/health",
        f"{TOURS_URL}/health", 
        f"{BOOKINGS_URL}/health"
    ]
    
    for service in services:
        if not wait_for_service(service, timeout=90):
            pytest.fail(f"Service not ready: {service}")
    
    print("All services are ready")
    return True

@pytest.fixture(scope="function")
def auth_token(services_ready):
    unique_id = int(time.time())
    user_data = TEST_USER.copy()
    user_data["username"] = f"testuser_{unique_id}"
    user_data["email"] = f"test{unique_id}@example.com"
    
    register_response = requests.post(f"{AUTH_URL}/users", json=user_data, timeout=10)
    if register_response.status_code != 201:
        pytest.fail(f"Failed to register user: {register_response.text}")
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    login_response = requests.post(f"{AUTH_URL}/login", json=login_data, timeout=10)
    if login_response.status_code != 200:
        pytest.fail(f"Failed to login: {login_response.text}")
    
    token = login_response.json()["access_token"]
    return token

@pytest.fixture(scope="function") 
def test_tour_id(auth_token):
    headers = get_auth_headers(auth_token)
    
    tour_data = TEST_TOUR.copy()
    tour_data["title"] = f"Test Tour {int(time.time())}"
    
    response = requests.post(f"{TOURS_URL}/tours", json=tour_data, headers=headers, timeout=10)
    if response.status_code != 201:
        pytest.fail(f"Failed to create tour: {response.text}")
    
    tour_data = response.json()
    return tour_data["id"]

class TestServiceIntegration:
    
    def test_services_health(self, services_ready):
        services = [
            (f"{AUTH_URL}/health", "auth-service"),
            (f"{TOURS_URL}/health", "tours-service"),
            (f"{BOOKINGS_URL}/health", "booking-service")
        ]
        
        for url, service_name in services:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"{service_name} health check failed"
            data = response.json()
            assert data["status"] == "healthy", f"{service_name} is unhealthy"
            print(f"Service {service_name}: {data}")

    def test_user_registration_flow(self, services_ready):
        user_data = {
            "username": f"integration_user_{int(time.time())}",
            "password": "integration_pass123",
            "email": f"integration{int(time.time())}@example.com", 
            "name": "Integration Test User",
            "phone": "+1987654321"
        }
        
        response = requests.post(f"{AUTH_URL}/users", json=user_data, timeout=10)
        assert response.status_code == 201, f"User registration failed: {response.text}"
        
        user_response = response.json()
        assert user_response["username"] == user_data["username"]
        assert user_response["email"] == user_data["email"]
        assert "id" in user_response
        print(f"User created: {user_response['username']}")

    def test_tour_creation_and_listing(self, auth_token, services_ready):
        headers = get_auth_headers(auth_token)
        
        response = requests.get(f"{TOURS_URL}/tours", timeout=10)
        assert response.status_code == 200
        tours = response.json()
        assert isinstance(tours, list)
        print(f"Tours received: {len(tours)}")
        
        new_tour = TEST_TOUR.copy()
        new_tour["title"] = f"Integration Tour {int(time.time())}"
        new_tour["destination"] = "Rome"
        
        response = requests.post(f"{TOURS_URL}/tours", json=new_tour, headers=headers, timeout=10)
        assert response.status_code == 201, f"Tour creation failed: {response.text}"
        
        created_tour = response.json()
        assert created_tour["title"] == new_tour["title"]
        assert created_tour["destination"] == new_tour["destination"]
        assert created_tour["available"] == True
        print(f"Tour created: {created_tour['title']}")

    def test_booking_creation_flow(self, auth_token, test_tour_id, services_ready):
        headers = get_auth_headers(auth_token)
        
        user_response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        
        tour_response = requests.get(f"{TOURS_URL}/tours/{test_tour_id}")
        assert tour_response.status_code == 200
        tour_data = tour_response.json()
        
        booking_data = {
            "title": tour_data["title"],
            "user_id": user_data["id"],
            "tour_id": test_tour_id,
            "travel_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "participants_count": 2,
            "contact_phone": user_data.get("phone", "+1234567890"),
            "contact_email": user_data["email"],
            "special_requests": "Test booking"
        }
        
        booking_response = requests.post(
            f"{BOOKINGS_URL}/bookings", 
            json=booking_data, 
            headers=headers,
            timeout=10
        )
        assert booking_response.status_code == 201, f"Booking creation failed: {booking_response.text}"
        
        booking = booking_response.json()
        assert booking["user_id"] == user_data["id"]
        assert booking["tour_id"] == test_tour_id
        assert booking["status"] == "pending"
        assert booking["payment_status"] == "pending"
        
        return booking["id"]

    def test_booking_confirmation_flow(self, auth_token, test_tour_id, services_ready):
        headers = get_auth_headers(auth_token)
        
        booking_id = self.test_booking_creation_flow(auth_token, test_tour_id, services_ready)
        
        confirm_response = requests.post(
            f"{BOOKINGS_URL}/bookings/{booking_id}/confirm",
            headers=headers,
            timeout=10
        )
        assert confirm_response.status_code == 200, f"Booking confirmation failed: {confirm_response.text}"
        
        confirmed_booking = confirm_response.json()
        assert confirmed_booking["status"] == "confirmed"
        assert confirmed_booking["payment_status"] == "paid"

    def test_booking_cancellation_flow(self, auth_token, test_tour_id, services_ready):
        headers = get_auth_headers(auth_token)
        
        booking_id = self.test_booking_creation_flow(auth_token, test_tour_id, services_ready)
        
        cancel_response = requests.put(
            f"{BOOKINGS_URL}/bookings/{booking_id}/cancel",
            headers=headers,
            timeout=10
        )
        assert cancel_response.status_code == 200, f"Booking cancellation failed: {cancel_response.text}"
        
        cancelled_booking = cancel_response.json()
        assert cancelled_booking["status"] == "cancelled"
        assert cancelled_booking["payment_status"] == "refunded"

    def test_user_bookings_list(self, auth_token, services_ready):
        headers = get_auth_headers(auth_token)
        
        user_response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        
        bookings_response = requests.get(
            f"{BOOKINGS_URL}/bookings/user/{user_data['id']}",
            headers=headers,
            timeout=10
        )
        assert bookings_response.status_code == 200
        bookings = bookings_response.json()
        assert isinstance(bookings, list)

    def test_tour_search_functionality(self, services_ready):
        response = requests.get(f"{TOURS_URL}/tours?destination=Paris", timeout=10)
        assert response.status_code == 200
        tours = response.json()
        assert isinstance(tours, list)

    def test_tour_availability_filter(self, services_ready):
        response = requests.get(f"{TOURS_URL}/tours?available=true", timeout=10)
        assert response.status_code == 200
        available_tours = response.json()
        
        for tour in available_tours:
            assert tour["available"] == True
        
        response_all = requests.get(f"{TOURS_URL}/tours", timeout=10)
        all_tours = response_all.json()
        
        assert len(available_tours) <= len(all_tours)

    def test_booking_statistics(self, auth_token, services_ready):
        headers = get_auth_headers(auth_token)
        
        response = requests.get(f"{BOOKINGS_URL}/bookings/stats", headers=headers, timeout=10)
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_bookings" in stats
        assert "pending_bookings" in stats
        assert "confirmed_bookings" in stats
        assert "cancelled_bookings" in stats
        assert "completed_bookings" in stats
        assert "total_revenue" in stats
        assert "average_booking_value" in stats
        
        assert stats["total_bookings"] >= 0
        assert stats["pending_bookings"] >= 0
        assert stats["confirmed_bookings"] >= 0
        assert stats["cancelled_bookings"] >= 0
        assert stats["completed_bookings"] >= 0
        assert float(stats["total_revenue"]) >= 0

class TestErrorScenarios:
    
    def test_duplicate_user_registration(self, services_ready):
        user_data = {
            "username": f"duplicate_test_{int(time.time())}",
            "password": "testpass123",
            "email": f"duplicate{int(time.time())}@example.com",
            "name": "Duplicate Test User"
        }
        
        response1 = requests.post(f"{AUTH_URL}/users", json=user_data, timeout=10)
        assert response1.status_code == 201
        
        response2 = requests.post(f"{AUTH_URL}/users", json=user_data, timeout=10)
        assert response2.status_code == 400
        
        user_data["username"] = f"different_username_{int(time.time())}"
        response3 = requests.post(f"{AUTH_URL}/users", json=user_data, timeout=10)
        assert response3.status_code == 400

    def test_invalid_authentication(self, services_ready):
        login_data = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }
        response = requests.post(f"{AUTH_URL}/login", json=login_data, timeout=10)
        assert response.status_code == 401

    def test_booking_nonexistent_tour(self, auth_token, services_ready):
        headers = get_auth_headers(auth_token)
        
        user_response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
        user_data = user_response.json()
        
        booking_data = {
            "title": "Nonexistent tour",
            "user_id": user_data["id"],
            "tour_id": 999999,
            "travel_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "participants_count": 1
        }
        
        response = requests.post(f"{BOOKINGS_URL}/bookings", json=booking_data, headers=headers, timeout=10)
        assert response.status_code == 404

    def test_unauthorized_tour_creation(self, services_ready):
        response = requests.post(f"{TOURS_URL}/tours", json=TEST_TOUR, timeout=10)
        assert response.status_code == 401

class TestPerformance:
    
    def test_multiple_parallel_requests(self, services_ready):
        import concurrent.futures
        
        def make_request(_):
            response = requests.get(f"{TOURS_URL}/tours", timeout=10)
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_request, range(10)))
        
        assert all(status == 200 for status in results)

    def test_response_time(self, services_ready):
        max_response_time = 2.0
        
        services = [
            f"{AUTH_URL}/health",
            f"{TOURS_URL}/tours",
            f"{BOOKINGS_URL}/health"
        ]
        
        for service_url in services:
            start_time = time.time()
            response = requests.get(service_url, timeout=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < max_response_time, f"Service {service_url} too slow: {response_time:.2f}s"
            assert response.status_code == 200

@pytest.mark.skipif(os.getenv("CI") != "true", reason="Only in CI environment")
class TestCISpecific:
    
    def test_ci_environment(self):
        assert os.getenv("CI") == "true", "This test should run only in CI"
        
    def test_k8s_cluster_running(self):
        result = subprocess.run(
            "kubectl cluster-info", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        assert result.returncode == 0, "Kubernetes cluster not available"
        
    def test_services_running(self):
        result = subprocess.run(
            "kubectl get pods -n tourism -o json", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        assert result.returncode == 0, "Failed to get pod information"
        
        import json
        pods_info = json.loads(result.stdout)
        running_pods = [
            pod for pod in pods_info["items"] 
            if pod["status"]["phase"] == "Running"
        ]
        assert len(running_pods) >= 3, "Not all services are running"