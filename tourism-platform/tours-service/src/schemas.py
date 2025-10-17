# tours-service/src/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TourCreate(BaseModel):
    title: str
    description: Optional[str] = None
    destination: str
    price: float
    duration_days: int
    available: bool = True
    # Use default_factory to avoid shared mutable default between instances
    features: Optional[List[str]] = None

class TourUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    available: Optional[bool] = None
    features: Optional[List[str]] = None

class Tour(BaseModel):
    id: int
    title: str
    description: Optional[str]
    destination: str
    price: float
    duration_days: int
    available: bool
    features: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True