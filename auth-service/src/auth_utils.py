# auth-service/src/auth_utils.py
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import os

# Секретный ключ и алгоритм читаем из окружения
SECRET_KEY = os.getenv("SECRET_KEY", "tourism-platform-secret-key-2024-production-ready")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Список администраторов (в реальном приложении это должно быть в базе данных)
ADMIN_USERS = ['admin', 'manager', 'root', 'boss']

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def verify_token(token: str):
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