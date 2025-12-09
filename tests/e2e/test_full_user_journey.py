import os
import time
import requests
import pytest


BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/")
AUTH_BASE = f"{BASE_URL}/api/auth"
TOURS_BASE = f"{BASE_URL}/api/tours"
BOOKINGS_BASE = f"{BASE_URL}/api/bookings"


def test_complete_booking_flow():
    """Минимальный E2E тест: регистрация -> логин -> просмотр туров -> бронирование."""
    unique_suffix = int(time.time())
    username = f"e2e_user_{unique_suffix}"
    password = "e2e_password_123"
    
    # 1. Регистрация
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "name": "E2E Test User",
        "phone": "+1234567890"
    }
    register_resp = requests.post(f"{AUTH_BASE}/users", json=register_payload, timeout=10)
    assert register_resp.status_code in (201, 400), f"Registration failed: {register_resp.text}"
    
    # 2. Логин
    login_resp = requests.post(f"{AUTH_BASE}/login", json={"username": username, "password": password}, timeout=10)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Просмотр туров
    tours_resp = requests.get(f"{TOURS_BASE}/tours", timeout=10)
    assert tours_resp.status_code == 200
    tours = tours_resp.json()
    assert isinstance(tours, list)
    
    # 4. Если есть доступные туры, пытаемся забронировать
    available_tours = [t for t in tours if t.get("available", False)]
    if available_tours:
        tour_id = available_tours[0]["id"]
        # Получаем информацию о пользователе
        me_resp = requests.get(f"{AUTH_BASE}/users/me", headers=headers, timeout=10)
        assert me_resp.status_code == 200
        user_data = me_resp.json()
        
        # Создаем бронирование
        booking_payload = {
            "title": available_tours[0]["title"],
            "user_id": user_data["id"],
            "tour_id": tour_id,
            "participants_count": 1,
            "travel_date": "2025-12-31T00:00:00",
            "contact_phone": user_data.get("phone", ""),
            "contact_email": user_data.get("email", "")
        }
        booking_resp = requests.post(f"{BOOKINGS_BASE}/bookings", json=booking_payload, headers=headers, timeout=10)
        # Может быть 201 (успех) или 404/503 (тур не найден или сервис недоступен)
        assert booking_resp.status_code in (201, 404, 503), f"Booking failed: {booking_resp.text}"


def test_user_registration_and_login():
    """Минимальный E2E тест: регистрация и вход пользователя."""
    unique_suffix = int(time.time())
    username = f"e2e_auth_{unique_suffix}"
    password = "test_pass_123"
    
    # Регистрация
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@test.com",
        "name": "Test User",
        "phone": "+1111111111"
    }
    register_resp = requests.post(f"{AUTH_BASE}/users", json=register_payload, timeout=10)
    assert register_resp.status_code in (201, 400)
    
    # Логин
    login_resp = requests.post(f"{AUTH_BASE}/login", json={"username": username, "password": password}, timeout=10)
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_tours_listing():
    """Минимальный E2E тест: просмотр списка туров через gateway."""
    try:
        response = requests.get(f"{TOURS_BASE}/tours", timeout=10)
        assert response.status_code == 200
        tours = response.json()
        assert isinstance(tours, list)
    except requests.RequestException:
        pytest.skip("Gateway or tours service not available")


def test_error_scenarios():
    """Минимальный E2E тест: проверка обработки ошибок."""
    # Неверный логин
    login_resp = requests.post(f"{AUTH_BASE}/login", json={"username": "nonexistent", "password": "wrong"}, timeout=10)
    assert login_resp.status_code == 401
    
    # Несуществующий тур
    try:
        tour_resp = requests.get(f"{TOURS_BASE}/tours/99999", timeout=10)
        assert tour_resp.status_code == 404
    except requests.RequestException:
        pytest.skip("Tours service not available")

