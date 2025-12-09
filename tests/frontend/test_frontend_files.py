"""Минимальные unit тесты для проверки структуры frontend файлов."""
import os
import pytest
from pathlib import Path


FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


def test_frontend_directory_exists():
    """Проверка: директория frontend существует."""
    assert FRONTEND_DIR.exists(), f"Frontend directory not found: {FRONTEND_DIR}"
    assert FRONTEND_DIR.is_dir()


def test_index_html_exists():
    """Проверка: файл index.html существует."""
    index_file = FRONTEND_DIR / "index.html"
    assert index_file.exists(), f"index.html not found in {FRONTEND_DIR}"
    assert index_file.is_file()


def test_script_js_exists():
    """Проверка: файл script.js существует."""
    script_file = FRONTEND_DIR / "script.js"
    assert script_file.exists(), f"script.js not found in {FRONTEND_DIR}"
    assert script_file.is_file()


def test_styles_css_exists():
    """Проверка: файл styles.css существует."""
    styles_file = FRONTEND_DIR / "styles.css"
    assert styles_file.exists(), f"styles.css not found in {FRONTEND_DIR}"
    assert styles_file.is_file()


def test_index_html_structure():
    """Проверка: базовая структура HTML в index.html."""
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        pytest.skip("index.html not found")
    
    content = index_file.read_text(encoding='utf-8')
    
    # Проверяем наличие основных элементов
    assert "<html" in content.lower() or "<!doctype" in content.lower()
    assert "<head" in content.lower()
    assert "<body" in content.lower()
    assert "Tourism Platform" in content or "tourism" in content.lower()


def test_script_js_not_empty():
    """Проверка: script.js не пустой."""
    script_file = FRONTEND_DIR / "script.js"
    if not script_file.exists():
        pytest.skip("script.js not found")
    
    content = script_file.read_text(encoding='utf-8')
    assert len(content.strip()) > 0, "script.js is empty"


def test_styles_css_not_empty():
    """Проверка: styles.css не пустой."""
    styles_file = FRONTEND_DIR / "styles.css"
    if not styles_file.exists():
        pytest.skip("styles.css not found")
    
    content = styles_file.read_text(encoding='utf-8')
    assert len(content.strip()) > 0, "styles.css is empty"


def test_script_js_has_functions():
    """Проверка: script.js содержит основные функции."""
    script_file = FRONTEND_DIR / "script.js"
    if not script_file.exists():
        pytest.skip("script.js not found")
    
    content = script_file.read_text(encoding='utf-8')
    
    # Проверяем наличие ключевых функций
    key_functions = [
        "function",
        "loadTours",
        "login",
        "registerUser"
    ]
    
    found_functions = [func for func in key_functions if func in content]
    assert len(found_functions) > 0, f"script.js should contain at least one key function. Found: {found_functions}"

