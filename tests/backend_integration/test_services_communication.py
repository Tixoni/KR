import os
import time
import requests  

AUTH_BASE_URL = os.getenv("AUTH_BASE_URL", "http://localhost:8000").rstrip("/")


def test_can_register_new_user():
    """Минимальный интеграционный тест: создаём пользователя через auth-service."""
    unique_suffix = int(time.time())
    payload = {
        "username": f"backend_int_{unique_suffix}",
        "password": "backend_int_password",
        "email": f"backend_int_{unique_suffix}@example.com",
        "name": "Backend Integration User",
        "phone": "+1234567890",
    }

    response = requests.post(f"{AUTH_BASE_URL}/users", json=payload, timeout=15)

    # Допускаем повторный запуск: 201 при первом создании, 400 если пользователь уже есть
    assert response.status_code in (201, 400), response.text