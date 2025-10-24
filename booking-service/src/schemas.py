from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class BookingCreate(BaseModel):
    title: str
    user_id: int
    tour_id: int
    travel_date: datetime
    participants_count: int = Field(ge=1, le=20, default=1)
    special_requests: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

class BookingUpdate(BaseModel):
    travel_date: Optional[datetime] = None
    participants_count: Optional[int] = Field(ge=1, le=20, default=None)
    special_requests: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

class BookingStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|cancelled|completed)$")
    payment_status: Optional[str] = Field(None, pattern="^(pending|paid|refunded)$")

class Booking(BaseModel):
    id: int
    user_id: int
    tour_id: int
    title: str
    booking_date: datetime
    travel_date: datetime
    participants_count: int
    total_price: Decimal
    status: str
    payment_status: str
    special_requests: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookingStats(BaseModel):
    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    completed_bookings: int
    total_revenue: Decimal
    average_booking_value: Decimal