# tours-service/src/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text
from sqlalchemy.types import JSON
from sqlalchemy.sql import func

# Импорт для работы в контейнере
from .database import Base

class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    destination = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    available = Column(Boolean, default=True)
    # JSON хорошо работает и в Postgres (jsonb), и в SQLite (хранится как TEXT)
    features = Column(JSON)
    images = Column(JSON)  # Массив URL фотографий
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())