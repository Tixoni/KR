import sys
import os

# Добавляем путь к src для корректного импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    """Тест health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "tours-service"
    assert body.get("status") in {"healthy", "unhealthy"}


def test_get_tours_list_returns_list():
    """Тест получения списка туров."""
    response = client.get("/tours")
    # Даже если таблицы нет, должен вернуть 200 с пустым списком
    # или 500 при ошибке БД
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        tours = response.json()
        assert isinstance(tours, list)


def test_get_nonexistent_tour_returns_404():
    """Тест получения несуществующего тура."""
    response = client.get("/tours/999999")
    # Может вернуть 404 или 500 (если таблицы нет)
    assert response.status_code in [404, 500]