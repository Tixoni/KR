"""Минимальные тесты для проверки API интеграции frontend."""
import os
import pytest


def test_frontend_api_endpoints_defined():
    """Проверка: frontend использует правильные API endpoints."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
    script_file = os.path.join(frontend_dir, "script.js")
    
    if not os.path.exists(script_file):
        pytest.skip("script.js not found")
    
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие API endpoints
    api_endpoints = [
        "/api/auth",
        "/api/tours",
        "/api/bookings"
    ]
    
    found_endpoints = [endpoint for endpoint in api_endpoints if endpoint in content]
    assert len(found_endpoints) > 0, f"script.js should reference API endpoints. Found: {found_endpoints}"


def test_frontend_uses_localstorage():
    """Проверка: frontend использует localStorage для токена."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
    script_file = os.path.join(frontend_dir, "script.js")
    
    if not os.path.exists(script_file):
        pytest.skip("script.js not found")
    
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем использование localStorage
    assert "localStorage" in content, "script.js should use localStorage for token management"

