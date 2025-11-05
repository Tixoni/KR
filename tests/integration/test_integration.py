import time
import requests


BASE_URL = "http://localhost"
GATEWAY_HEALTH = f"{BASE_URL}/health"
AUTH_BASE = f"{BASE_URL}/api/auth"
TOURS_BASE = f"{BASE_URL}/api/tours"
BOOKINGS_BASE = f"{BASE_URL}/api/bookings"


def wait_for_gateway_ready(timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            resp = requests.get(GATEWAY_HEALTH, timeout=3)
            if resp.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("Gateway did not become ready in time")


def test_gateway_and_services_health():
    wait_for_gateway_ready()

    # Gateway health
    r = requests.get(GATEWAY_HEALTH, timeout=3)
    assert r.status_code == 200
    assert "healthy" in r.text

    # Downstream services via gateway
    # Endpoints inferred from gateway nginx config and k8s probes
    for path in [
        "/api/auth/health",
        "/api/tours/health",
        "/api/bookings/health",
    ]:
        resp = requests.get(f"{BASE_URL}{path}", timeout=5)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "healthy"


def test_auth_register_login_me_flow():
    wait_for_gateway_ready()

    # register
    payload = {
        "username": "int_user",
        "password": "int_pass_123",
        "email": "int_user@example.com",
        "name": "Integration User",
        "phone": "+10000000000"
    }
    r = requests.post(f"{AUTH_BASE}/users", json=payload, timeout=10)
    # allow 201 (created) or 400 if already exists
    assert r.status_code in (201, 400)

    # login
    r = requests.post(f"{AUTH_BASE}/login", json={"username": payload["username"], "password": payload["password"]}, timeout=10)
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # users/me
    r = requests.get(f"{AUTH_BASE}/users/me", headers=headers, timeout=10)
    assert r.status_code == 200
    me = r.json()
    assert me.get("username") == payload["username"]


def test_list_tours_and_bookings_health_endpoints():
    wait_for_gateway_ready()

    # Tours list should be reachable (may be empty)
    rt = requests.get(f"{TOURS_BASE}/tours", timeout=10)
    assert rt.status_code == 200

    # Bookings health reachable
    rb = requests.get(f"{BOOKINGS_BASE}/health", timeout=10)
    assert rb.status_code == 200


