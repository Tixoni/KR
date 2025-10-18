# booking-service/src/auth_utils.py
from jose import JWTError, jwt
from fastapi import HTTPException, status
import os
import httpx

# Секретный ключ и алгоритм читаем из окружения (должны совпадать с auth-service)
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

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

async def get_user_from_auth_service(user_id: int, token: str = None):
    """Получает информацию о пользователе из auth-service"""
    try:
        async with httpx.AsyncClient() as client:
            # В Docker compose используем имя сервиса
            auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            url = f"{auth_service_url}/users/{user_id}"
            print(f"Запрос к auth-service: {url}")
            print(f"Заголовки: {headers}")
            
            response = await client.get(url, headers=headers)
            print(f"Ответ от auth-service: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"Данные пользователя: {user_data}")
                return user_data
            else:
                print(f"Ошибка от auth-service: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Ошибка получения пользователя из auth-service: {e}")
        return None

async def validate_user_exists(user_id: int, token: str = None):
    """Проверяет существование пользователя в auth-service"""
    print(f"Проверяем существование пользователя {user_id} с токеном: {token[:20] if token else 'None'}...")
    user = await get_user_from_auth_service(user_id, token)
    print(f"Результат проверки пользователя: {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
