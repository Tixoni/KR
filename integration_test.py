import os
import time
import requests


BASE_AUTH = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
BASE_TOURS = os.getenv("TOURS_BASE_URL", "http://localhost:8001")
BASE_BOOKING = os.getenv("BOOKING_BASE_URL", "http://localhost:8002")


def wait_for_service(url: str, timeout_seconds: int = 60) -> None:
    start = time.time()
    last_error = None
    while time.time() - start < timeout_seconds:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return
            last_error = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001 - simple polling helper
            last_error = str(e)
        time.sleep(2)
    raise AssertionError(f"Service {url} did not become healthy in time: {last_error}")


def test_health_endpoints_up():
    wait_for_service(f"{BASE_AUTH}/health")
    wait_for_service(f"{BASE_TOURS}/health")
    wait_for_service(f"{BASE_BOOKING}/health")

    a = requests.get(f"{BASE_AUTH}/health").json()
    t = requests.get(f"{BASE_TOURS}/health").json()
    b = requests.get(f"{BASE_BOOKING}/health").json()

    assert a.get("service") == "auth-service"
    assert t.get("service") == "tours-service"
    assert b.get("service") == "booking-service"


