from fastapi.testclient import TestClient

from src import main as app_main  # type: ignore


client = TestClient(app_main.app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "tours-service"
    assert body.get("status") in {"healthy", "unhealthy"}


def test_get_tours_list_ok():
    response = client.get("/tours")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


