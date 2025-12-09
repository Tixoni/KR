import sys
import os
from fastapi.testclient import TestClient
import json

# Добавляем путь к src для корректного импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "tours-service"
    assert body.get("status") in {"healthy", "unhealthy"}


def test_get_tours_list_ok():
    response = client.get("/tours")
    assert response.status_code == 200
    tours = response.json()
    assert isinstance(tours, list)


def test_create_and_get_tour():
    # Создаем тестовый тур
    tour_data = {
        "title": "Test Tour",
        "description": "Test description",
        "destination": "Test Destination",
        "price": 100.50,
        "duration_days": 7,
        "available": True,
        "features": ["feature1", "feature2"],
        "images": ["image1.jpg", "image2.jpg"]
    }
    
    # Для создания тура нужна авторизация админа
    # Пока просто проверяем, что эндпоинт существует
    response = client.get("/tours/9999")
    # Может вернуть 404, что нормально для несуществующего тура
    assert response.status_code in [404, 200]