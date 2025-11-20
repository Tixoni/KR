import pytest
import requests
import time
from datetime import datetime, timedelta
import json

# Базовые URL сервисов через gateway
BASE_URL = "http://localhost:8080/api"
AUTH_URL = f"{BASE_URL}/auth"
TOURS_URL = f"{BASE_URL}/tours"
BOOKINGS_URL = f"{BASE_URL}/bookings"

# Тестовые данные
TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "password": "testpass123",
    "email": f"test{int(time.time())}@example.com",
    "name": "Test User",
    "phone": "+1234567890"
}

TEST_TOUR = {
    "title": "Тестовый тур в Париж",
    "destination": "Париж",
    "price": 50000.0,
    "duration_days": 7,
    "description": "Экскурсионный тур по Парижу",
    "features": ["Экскурсии", "Трансфер", "Завтраки"],
    "available": True
}

def wait_for_service(url: str, timeout: int = 60):
    """Ожидание доступности сервиса"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    return False

def get_auth_headers(token: str):
    """Получение заголовков с авторизацией"""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

@pytest.fixture(scope="module")
def auth_token():
    """Фикстура для получения токена аутентификации"""
    # Ожидаем доступности сервисов
    assert wait_for_service(f"{AUTH_URL}/health"), "Auth service not available"
    assert wait_for_service(f"{TOURS_URL}/health"), "Tours service not available"
    assert wait_for_service(f"{BOOKINGS_URL}/health"), "Booking service not available"
    
    # Регистрируем пользователя
    register_response = requests.post(f"{AUTH_URL}/users", json=TEST_USER)
    if register_response.status_code != 201:
        # Если пользователь уже существует, пробуем другой username
        TEST_USER["username"] = f"testuser_{int(time.time())}"
        TEST_USER["email"] = f"test{int(time.time())}@example.com"
        register_response = requests.post(f"{AUTH_URL}/users", json=TEST_USER)
        assert register_response.status_code == 201, f"Failed to register user: {register_response.text}"
    
    # Логинимся
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    login_response = requests.post(f"{AUTH_URL}/login", json=login_data)
    assert login_response.status_code == 200, f"Failed to login: {login_response.text}"
    
    token = login_response.json()["access_token"]
    return token

@pytest.fixture(scope="module")
def test_tour_id(auth_token):
    """Фикстура для создания тестового тура"""
    headers = get_auth_headers(auth_token)
    
    # Создаем тур
    response = requests.post(f"{TOURS_URL}/tours", json=TEST_TOUR, headers=headers)
    assert response.status_code == 201, f"Failed to create tour: {response.text}"
    
    tour_data = response.json()
    return tour_data["id"]

class TestServiceIntegration:
    """Тесты интеграции между сервисами"""
    
    def test_services_health(self):
        """Тест здоровья всех сервисов"""
        services = [
            (f"{AUTH_URL}/health", "auth-service"),
            (f"{TOURS_URL}/health", "tours-service"),
            (f"{BOOKINGS_URL}/health", "booking-service")
        ]
        
        for url, service_name in services:
            response = requests.get(url)
            assert response.status_code == 200, f"{service_name} health check failed"
            data = response.json()
            assert data["status"] == "healthy", f"{service_name} is unhealthy"
            assert data["database"] == "connected", f"{service_name} database disconnected"
    
    def test_user_registration_flow(self):
        """Тест полного цикла регистрации пользователя"""
        # Регистрируем нового пользователя
        user_data = {
            "username": f"integration_user_{int(time.time())}",
            "password": "integration_pass123",
            "email": f"integration{int(time.time())}@example.com",
            "name": "Integration Test User",
            "phone": "+1987654321"
        }
        
        response = requests.post(f"{AUTH_URL}/users", json=user_data)
        assert response.status_code == 201, f"User registration failed: {response.text}"
        
        user_response = response.json()
        assert user_response["username"] == user_data["username"]
        assert user_response["email"] == user_data["email"]
        assert "id" in user_response
    
    def test_tour_creation_and_listing(self, auth_token):
        """Тест создания и получения туров"""
        headers = get_auth_headers(auth_token)
        
        # Получаем список туров
        response = requests.get(f"{TOURS_URL}/tours")
        assert response.status_code == 200
        tours = response.json()
        assert isinstance(tours, list)
        
        # Создаем новый тур
        new_tour = TEST_TOUR.copy()
        new_tour["title"] = f"Интеграционный тур {int(time.time())}"
        new_tour["destination"] = "Рим"
        
        response = requests.post(f"{TOURS_URL}/tours", json=new_tour, headers=headers)
        assert response.status_code == 201, f"Tour creation failed: {response.text}"
        
        created_tour = response.json()
        assert created_tour["title"] == new_tour["title"]
        assert created_tour["destination"] == new_tour["destination"]
        assert created_tour["available"] == True
    
    def test_booking_creation_flow(self, auth_token, test_tour_id):
        """Тест полного цикла бронирования"""
        headers = get_auth_headers(auth_token)
        
        # Получаем информацию о пользователе
        user_response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        
        # Получаем информацию о туре
        tour_response = requests.get(f"{TOURS_URL}/tours/{test_tour_id}")
        assert tour_response.status_code == 200
        tour_data = tour_response.json()
        
        # Создаем бронирование
        booking_data = {
            "title": tour_data["title"],
            "user_id": user_data["id"],
            "tour_id": test_tour_id,
            "travel_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "participants_count": 2,
            "contact_phone": user_data.get("phone", "+1234567890"),
            "contact_email": user_data["email"],
            "special_requests": "Тестовое бронирование"
        }
        
        booking_response = requests.post(
            f"{BOOKINGS_URL}/bookings", 
            json=booking_data, 
            headers=headers
        )
        assert booking_response.status_code == 201, f"Booking creation failed: {booking_response.text}"
        
        booking = booking_response.json()
        assert booking["user_id"] == user_data["id"]
        assert booking["tour_id"] == test_tour_id
        assert booking["status"] == "pending"
        assert booking["payment_status"] == "pending"
        
        return booking["id"]
    
    def test_booking_confirmation_flow(self, auth_token, test_tour_id):
        """Тест подтверждения бронирования"""
        headers = get_auth_headers(auth_token)
        
        # Создаем бронирование
        booking_id = self.test_booking_creation_flow(auth_token, test_tour_id)
        
        # Подтверждаем бронирование
        confirm_response = requests.post(
            f"{BOOKINGS_URL}/bookings/{booking_id}/confirm",
            headers=headers
        )
        assert confirm_response.status_code == 200, f"Booking confirmation failed: {confirm_response.text}"
        
        confirmed_booking = confirm_response.json()
        assert confirmed_booking["status"] == "confirmed"
        assert confirmed_booking["payment_status"] == "paid"
    
    def test_booking_cancellation_flow(self, auth_token, test_tour_id):
        """Тест отмены бронирования"""
        headers = get_auth_headers(auth_token)
        
        # Создаем новое бронирование для отмены
        booking_id = self.test_booking_creation_flow(auth_token, test_tour_id)
        
        # Отменяем бронирование
        cancel_response = requests.put(
            f"{BOOKINGS_URL}/bookings/{booking_id}/cancel",
            headers=headers
        )
        assert cancel_response.status_code == 200, f"Booking cancellation failed: {cancel_response.text}"
        
        cancelled_booking = cancel_response.json()
        assert cancelled_booking["status"] == "cancelled"
        assert cancelled_booking["payment_status"] == "refunded"
    
    def test_user_bookings_list(self, auth_token, test_tour_id):
        """Тест получения списка бронирований пользователя"""
        headers = get_auth_headers(auth_token)
        
        # Получаем информацию о пользователе
        user_response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        
        # Получаем бронирования пользователя
        bookings_response = requests.get(
            f"{BOOKINGS_URL}/bookings/user/{user_data['id']}",
            headers=headers
        )
        assert bookings_response.status_code == 200
        bookings = bookings_response.json()
        assert isinstance(bookings, list)
    
    def test_tour_search_functionality(self):
        """Тест поиска туров по направлению"""
        # Ищем туры по направлению
        response = requests.get(f"{TOURS_URL}/tours?destination=Париж")
        assert response.status_code == 200
        tours = response.json()
        assert isinstance(tours, list)
        
        # Если есть туры, проверяем что они содержат искомое направление
        if tours:
            for tour in tours:
                assert "Париж" in tour["destination"]
    
    def test_tour_availability_filter(self):
        """Тест фильтрации туров по доступности"""
        # Получаем только доступные туры
        response = requests.get(f"{TOURS_URL}/tours?available=true")
        assert response.status_code == 200
        available_tours = response.json()
        
        for tour in available_tours:
            assert tour["available"] == True
        
        # Получаем все туры (без фильтра)
        response_all = requests.get(f"{TOURS_URL}/tours")
        all_tours = response_all.json()
        
        # Проверяем что доступных туров не больше чем всех
        assert len(available_tours) <= len(all_tours)
    
    def test_booking_statistics(self, auth_token):
        """Тест получения статистики бронирований"""
        headers = get_auth_headers(auth_token)
        
        response = requests.get(f"{BOOKINGS_URL}/bookings/stats", headers=headers)
        assert response.status_code == 200
        stats = response.json()
        
        # Проверяем структуру ответа
        assert "total_bookings" in stats
        assert "pending_bookings" in stats
        assert "confirmed_bookings" in stats
        assert "cancelled_bookings" in stats
        assert "completed_bookings" in stats
        assert "total_revenue" in stats
        assert "average_booking_value" in stats
        
        # Проверяем что значения неотрицательные
        assert stats["total_bookings"] >= 0
        assert stats["pending_bookings"] >= 0
        assert stats["confirmed_bookings"] >= 0
        assert stats["cancelled_bookings"] >= 0
        assert stats["completed_bookings"] >= 0
        assert float(stats["total_revenue"]) >= 0

class TestErrorScenarios:
    """Тесты обработки ошибок и пограничных случаев"""
    
    def test_duplicate_user_registration(self):
        """Тест регистрации дубликата пользователя"""
        user_data = {
            "username": f"duplicate_test_{int(time.time())}",
            "password": "testpass123",
            "email": f"duplicate{int(time.time())}@example.com",
            "name": "Duplicate Test User"
        }
        
        # Первая регистрация - должна быть успешной
        response1 = requests.post(f"{AUTH_URL}/users", json=user_data)
        assert response1.status_code == 201
        
        # Вторая регистрация с тем же username - должна вернуть ошибку
        response2 = requests.post(f"{AUTH_URL}/users", json=user_data)
        assert response2.status_code == 400
        
        # Вторая регистрация с тем же email - должна вернуть ошибку
        user_data["username"] = f"different_username_{int(time.time())}"
        response3 = requests.post(f"{AUTH_URL}/users", json=user_data)
        assert response3.status_code == 400
    
    def test_invalid_authentication(self):
        """Тест невалидной аутентификации"""
        # Неправильный пароль
        login_data = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }
        response = requests.post(f"{AUTH_URL}/login", json=login_data)
        assert response.status_code == 401
    
    def test_booking_nonexistent_tour(self, auth_token):
        """Тест бронирования несуществующего тура"""
        headers = get_auth_headers(auth_token)
        
        # Получаем информацию о пользователе
        user_response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
        user_data = user_response.json()
        
        booking_data = {
            "title": "Несуществующий тур",
            "user_id": user_data["id"],
            "tour_id": 999999,  # Несуществующий ID
            "travel_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "participants_count": 1
        }
        
        response = requests.post(f"{BOOKINGS_URL}/bookings", json=booking_data, headers=headers)
        assert response.status_code == 404  # Тур не найден
    
    def test_unauthorized_tour_creation(self):
        """Тест создания тура без авторизации"""
        response = requests.post(f"{TOURS_URL}/tours", json=TEST_TOUR)
        assert response.status_code == 401  # Не авторизован

class TestPerformance:
    """Тесты производительности и параллельных запросов"""
    
    def test_multiple_parallel_requests(self):
        """Тест множественных параллельных запросов"""
        import concurrent.futures
        
        def make_request(_):
            response = requests.get(f"{TOURS_URL}/tours", timeout=10)
            return response.status_code
        
        # Делаем 10 параллельных запросов
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_request, range(10)))
        
        # Все запросы должны быть успешными
        assert all(status == 200 for status in results)
    
    def test_response_time(self):
        """Тест времени ответа сервисов"""
        max_response_time = 2.0  # секунды
        
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

# Запуск тестов
if __name__ == "__main__":
    pytest.main([__file__, "-v"])