import sys
import os
from fastapi.testclient import TestClient
import uuid

# Добавляем путь к src для корректного импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "auth-service"
    assert body.get("status") in {"healthy", "unhealthy"}


def test_create_user_returns_created_user():
    unique_username = f"user_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": unique_username,
        "password": "secret123",
        "email": f"{unique_username}@example.com",
        "name": "Test User",
        "phone": "+1234567890",
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "password" not in data
    assert data["id"] > 0

