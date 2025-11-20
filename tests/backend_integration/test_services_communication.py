import pytest
import requests
import time
import os
from datetime import datetime, timedelta

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8080/api")

def is_service_available():
    """Проверяет доступность сервиса"""
    try:
        response = requests.get(f"{BASE_URL}/auth/health", timeout=5)
        return response.status_code == 200
    except:
        return False

@pytest.fixture(scope="session")
def services_ready():
    """Фикстура проверки готовности сервисов"""
    if not is_service_available():
        pytest.skip("Services not available")
    return True

def get_auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json"
    }

class TestBasicIntegration:
    """Базовые тесты интеграции"""
    
    def test_services_health(self, services_ready):
        """Тест здоровья сервисов"""
        services = ["auth", "tours", "bookings"]
        
        for service in services:
            response = requests.get(f"{BASE_URL}/{service}/health", timeout=10)
            assert response.status_code == 200, f"{service} health check failed"
            data = response.json()
            assert data["status"] == "healthy", f"{service} is unhealthy"

    def test_user_registration(self, services_ready):
        """Тест регистрации пользователя"""
        user_data = {
            "username": f"test_user_{int(time.time())}",
            "password": "test_password",
            "email": f"test{int(time.time())}@example.com",
            "name": "Test User"
        }
        
        response = requests.post(f"{BASE_URL}/auth/users", json=user_data, timeout=10)
        assert response.status_code in [201, 400]  # 201 created or 400 if exists
        
        if response.status_code == 201:
            user = response.json()
            assert user["username"] == user_data["username"]

    def test_tours_list(self, services_ready):
        """Тест получения списка туров"""
        response = requests.get(f"{BASE_URL}/tours/tours", timeout=10)
        assert response.status_code == 200
        tours = response.json()
        assert isinstance(tours, list)

class TestAuthenticatedFlows:
    """Тесты требующие аутентификации"""
    
    @pytest.fixture
    def auth_token(self, services_ready):
        """Фикстура для получения токена"""
        # Создаем уникального пользователя
        username = f"auth_user_{int(time.time())}"
        user_data = {
            "username": username,
            "password": "test_pass",
            "email": f"{username}@example.com",
            "name": "Auth Test User"
        }
        
        # Регистрируем
        requests.post(f"{BASE_URL}/auth/users", json=user_data, timeout=10)
        
        # Логинимся
        login_data = {"username": username, "password": "test_pass"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            pytest.skip("Failed to get auth token")

    def test_user_profile(self, services_ready, auth_token):
        """Тест получения профиля пользователя"""
        headers = get_auth_headers(auth_token)
        response = requests.get(f"{BASE_URL}/auth/users/me", headers=headers, timeout=10)
        assert response.status_code == 200
        user_data = response.json()
        assert "username" in user_data
        assert "email" in user_data

    def test_tour_creation(self, services_ready, auth_token):
        """Тест создания тура"""
        headers = get_auth_headers(auth_token)
        
        tour_data = {
            "title": f"Test Tour {int(time.time())}",
            "destination": "Test Destination",
            "price": 100.0,
            "duration_days": 3,
            "available": True
        }
        
        response = requests.post(f"{BASE_URL}/tours/tours", json=tour_data, headers=headers, timeout=10)
        # Может вернуть 201 или 403 если нет прав
        assert response.status_code in [201, 403]

class TestErrorScenarios:
    """Тесты обработки ошибок"""
    
    def test_invalid_login(self, services_ready):
        """Тест неверных учетных данных"""
        login_data = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        assert response.status_code == 401

    def test_unauthorized_access(self, services_ready):
        """Тест неавторизованного доступа"""
        response = requests.post(f"{BASE_URL}/tours/tours", json={}, timeout=10)
        assert response.status_code == 401

@pytest.mark.skipif(not os.getenv("CI"), reason="Run only in CI")
class TestCISpecific:
    """CI-специфичные тесты"""
    
    def test_environment_variables(self):
        """Тест переменных окружения"""
        assert os.getenv("CI") == "true"
        
    def test_service_endpoints(self, services_ready):
        """Тест доступности эндпоинтов"""
        endpoints = [
            f"{BASE_URL}/auth/health",
            f"{BASE_URL}/tours/health", 
            f"{BASE_URL}/bookings/health"
        ]
        
        for endpoint in endpoints:
            response = requests.get(endpoint, timeout=10)
            assert response.status_code == 200