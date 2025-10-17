from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .database import Base

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tour_id = Column(Integer, nullable=False, index=True)
    
    # Основная информация о бронировании
    booking_date = Column(DateTime(timezone=True), server_default=func.now())
    travel_date = Column(DateTime(timezone=True), nullable=False)
    participants_count = Column(Integer, nullable=False, default=1)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Статусы как строки (ENUM в БД будет валидировать значения)
    status = Column(String(20), default="pending")
    payment_status = Column(String(20), default="pending")
    
    # Дополнительная информация
    special_requests = Column(Text)
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Методы для удобства
    def is_cancelled(self):
        return self.status == "cancelled"
    
    def is_confirmed(self):
        return self.status == "confirmed"
    
    def is_pending(self):
        return self.status == "pending"