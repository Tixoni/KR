import pytest
import sys
import os
from pathlib import Path

# Добавляем родительский каталог в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from main import app
from database import Base
import utils

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import database
database.engine = engine

import main
main.engine = engine

import routes
routes.SessionLocal = TestingSessionLocal

# Импортируем get_db после переопределения engine
from database import get_db

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "password": "testpassword123"
    }

class TestUserRegistration:
    """Тесты регистрации пользователей"""
    
    def test_register_success(self, client, setup_database, test_user_data):
        """Успешная регистрация нового пользователя"""
        response = client.post("/register", json=test_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
    
    def test_register_duplicate_user(self, client, setup_database, test_user_data):
        """Попытка зарегистрировать существующего пользователя"""

        client.post("/register", json=test_user_data)
        
        response = client.post("/register", json=test_user_data)
        assert response.status_code == 400
        assert "User already exists" in response.json()["detail"]
    
    def test_register_invalid_data(self, client, setup_database):
        """Регистрация с некорректными данными"""
        invalid_data = {"username": "", "password": "123"}
        response = client.post("/register", json=invalid_data)
        assert response.status_code == 400

class TestUserLogin:
    """Тесты входа пользователей"""
    
    def test_login_success(self, client, setup_database, test_user_data):
        """Успешный вход пользователя"""

        client.post("/register", json=test_user_data)
        
        response = client.post("/login", json=test_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self, client, setup_database):
        """Вход с неверными учетными данными"""
        invalid_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/login", json=invalid_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_wrong_password(self, client, setup_database, test_user_data):
        """Вход с неверным паролем"""

        client.post("/register", json=test_user_data)
        
        wrong_password_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        response = client.post("/login", json=wrong_password_data)
        assert response.status_code == 401

class TestSessionManagement:
    """Тесты управления сессиями"""
    
    def test_check_session_valid_token(self, client, setup_database, test_user_data):
        """Проверка валидного токена"""

        client.post("/register", json=test_user_data)
        login_response = client.post("/login", json=test_user_data)
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/check-session", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert data["username"] == test_user_data["username"]
    
    def test_check_session_invalid_token(self, client, setup_database):
        """Проверка невалидного токена"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/check-session", headers=headers)
        assert response.status_code == 401
    
    def test_check_session_no_token(self, client, setup_database):
        """Проверка без токена"""
        response = client.get("/check-session")
        assert response.status_code == 401
    
    def test_check_session_expired_token(self, client, setup_database, test_user_data):
        """Проверка истекшего токена"""

        with patch.dict(os.environ, {"JWT_EXPIRES_IN": "1"}), \
             patch('time.time', return_value=0):
            
            client.post("/register", json=test_user_data)
            login_response = client.post("/login", json=test_user_data)
            token = login_response.json()["access_token"]
            
            import time
            time.sleep(2)
            
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/check-session", headers=headers)
            assert response.status_code == 401

class TestLogout:
    """Тесты выхода из системы"""
    
    def test_logout_success(self, client, setup_database, test_user_data):
        """Успешный выход"""
        response = client.post("/logout")
        assert response.status_code == 200
        assert "Logged out" in response.json()["message"]

class TestPasswordHashing:
    """Тесты хеширования паролей"""
    
    def test_hash_password(self):
        """Тест хеширования пароля"""
        password = "testpassword123"
        hashed = utils.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password_correct(self):
        """Тест проверки правильного пароля"""
        password = "testpassword123"
        hashed = utils.hash_password(password)
        
        assert utils.verify_password(password, hashed) == True
    
    def test_verify_password_incorrect(self):
        """Тест проверки неправильного пароля"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = utils.hash_password(password)
        
        assert utils.verify_password(wrong_password, hashed) == False
    
    def test_hash_password_different_salts(self):
        """Тест что одинаковые пароли дают разные хеши"""
        password = "testpassword123"
        hashed1 = utils.hash_password(password)
        hashed2 = utils.hash_password(password)
        
        assert hashed1 != hashed2

        assert utils.verify_password(password, hashed1) == True
        assert utils.verify_password(password, hashed2) == True

class TestHealthCheck:
    """Тесты проверки здоровья сервиса"""
    
    def test_health_check(self, client):
        """Проверка эндпоинта здоровья"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-service"

class TestIntegration:
    """Интеграционные тесты полного цикла"""
    
    def test_full_user_lifecycle(self, client, setup_database):
        """Полный жизненный цикл пользователя"""
        user_data = {
            "username": "lifecycleuser",
            "password": "lifecyclepass123"
        }
        
        register_response = client.post("/register", json=user_data)
        assert register_response.status_code == 200
        
        login_response = client.post("/login", json=user_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        session_response = client.get("/check-session", headers=headers)
        assert session_response.status_code == 200
        
        logout_response = client.post("/logout")
        assert logout_response.status_code == 200
        
        session_response_after_logout = client.get("/check-session", headers=headers)

        assert session_response_after_logout.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
