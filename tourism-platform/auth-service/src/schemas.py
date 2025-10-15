# auth-service/src/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    name: str
    phone: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    name: str
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str