import sys
import os
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from decimal import Decimal

# Добавляем путь к src для корректного импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "booking-service"
    assert body.get("status") in {"healthy", "unhealthy"}


def test_create_booking_calculates_total_price(monkeypatch):
    async def _fake_validate_user(user_id: int, token: str = None):
        return {"id": user_id, "username": "user"}

    async def _fake_get_tour_price(tour_id: int) -> Decimal:
        return Decimal("150.50")

    # ИСПРАВЛЕНО: Правильный путь к модулю
    monkeypatch.setattr("src.auth_utils.validate_user_exists", _fake_validate_user)
    monkeypatch.setattr("src.main.get_tour_price", _fake_get_tour_price)

    payload = {
        "title": "Test booking",
        "user_id": 1,
        "tour_id": 42,
        "travel_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "participants_count": 2,
        "contact_email": "user@example.com",
        "contact_phone": "+1234567890",
    }

    response = client.post(
        "/bookings",
        json=payload,
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["user_id"] == payload["user_id"]
    assert body["tour_id"] == payload["tour_id"]
    assert Decimal(str(body["total_price"])) == Decimal("301.00")