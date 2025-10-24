# tours-service/src/auth_utils.py
from jose import JWTError, jwt
import os

# Секретный ключ и алгоритм читаем из окружения (должны совпадать с auth-service)
SECRET_KEY = os.getenv("SECRET_KEY", "tourism-platform-secret-key-2024-production-ready")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Список администраторов (должен совпадать с auth-service)
ADMIN_USERS = ['admin', 'manager', 'root', 'boss']

def verify_token(token: str):
    """Проверяет JWT токен и возвращает username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

def is_admin_user(username: str) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return username in ADMIN_USERS
