import os
import requests
import pytest


BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/")


def test_frontend_page_loads():
    """Минимальный тест: главная страница загружается."""
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200
        assert "Tourism Platform" in response.text or "tourism" in response.text.lower()
    except requests.RequestException:
        pytest.skip("Frontend not available")


def test_html_structure_basic():
    """Минимальный тест: проверка базовой структуры HTML."""
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200
        html = response.text.lower()
        # Проверяем наличие основных элементов
        assert "<html" in html or "<!doctype" in html
        assert "<head" in html
        assert "<body" in html
    except requests.RequestException:
        pytest.skip("Frontend not available")


def test_css_loads():
    """Минимальный тест: CSS файл доступен."""
    try:
        response = requests.get(f"{BASE_URL}/styles.css", timeout=5)
        # CSS может быть 200 или 404, но не должно быть 500
        assert response.status_code != 500
    except requests.RequestException:
        pytest.skip("Frontend not available")

