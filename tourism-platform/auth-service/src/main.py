# auth-service/src/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import bcrypt

from . import models, schemas
from .database import SessionLocal, engine, get_db

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth Service",
    description="Microservice for authentication and user management",
    version="1.0.0"
)

# Функция для хеширования пароля
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}

# Get all users
@app.get("/users", response_model=List[schemas.UserResponse])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# Get user by ID
@app.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Create new user (регистрация)
@app.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | 
        (models.User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Username or email already exists"
        )
    
    # Хешируем пароль
    hashed_password = hash_password(user.password)
    
    db_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        email=user.email,
        name=user.name,
        phone=user.phone
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login endpoint (для будущего использования)
@app.post("/login")
async def login():
    # TODO: Реализовать логику входа
    return {"message": "Login endpoint - to be implemented"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)