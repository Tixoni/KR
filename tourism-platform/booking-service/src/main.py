# booking-service/src/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# Импорты для работы в контейнере
from .models import Booking as BookingModel
from .schemas import (
    BookingCreate, BookingUpdate, BookingStatusUpdate, 
    Booking as BookingSchema, BookingStats
)
from .database import SessionLocal, engine, get_db

# Таблицы создаются в init.sql при инициализации БД

app = FastAPI(
    title="Booking Service",
    description="Microservice for managing tour bookings",
    version="1.0.0"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "booking-service"}

# Вспомогательная функция для получения цены тура
def get_tour_price(tour_id: int) -> Decimal:
    # В реальном приложении здесь был бы запрос к tours-service
    # Пока возвращаем фиксированную цену для демонстрации
    return Decimal("100.00")

# POST /bookings - создать бронирование
@app.post("/bookings", response_model=BookingSchema, status_code=status.HTTP_201_CREATED)
async def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    try:
        # Получаем цену тура (в реальном приложении - запрос к tours-service)
        tour_price = get_tour_price(booking.tour_id)
        total_price = tour_price * booking.participants_count
        
        db_booking = BookingModel(
            user_id=booking.user_id,
            tour_id=booking.tour_id,
            travel_date=booking.travel_date,
            participants_count=booking.participants_count,
            total_price=total_price,
            special_requests=booking.special_requests,
            contact_phone=booking.contact_phone,
            contact_email=booking.contact_email
        )
        
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating booking: {str(e)}")

# GET /bookings/{id} - получить бронирование по ID
@app.get("/bookings/{booking_id}", response_model=BookingSchema)
async def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

# GET /bookings/user/{user_id} - бронирования пользователя
@app.get("/bookings/user/{user_id}", response_model=List[BookingSchema])
async def get_user_bookings(
    user_id: int, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(BookingModel).filter(BookingModel.user_id == user_id)
    
    if status_filter:
        query = query.filter(BookingModel.status == status_filter)
    
    bookings = query.offset(skip).limit(limit).all()
    return bookings

# GET /bookings/tour/{tour_id} - бронирования конкретного тура
@app.get("/bookings/tour/{tour_id}", response_model=List[BookingSchema])
async def get_tour_bookings(
    tour_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    bookings = db.query(BookingModel).filter(
        BookingModel.tour_id == tour_id
    ).offset(skip).limit(limit).all()
    return bookings

# PUT /bookings/{id} - обновить бронирование
@app.put("/bookings/{booking_id}", response_model=BookingSchema)
async def update_booking(
    booking_id: int, 
    booking_update: BookingUpdate, 
    db: Session = Depends(get_db)
):
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot update cancelled booking")
    
    update_data = booking_update.model_dump(exclude_unset=True)
    
    # Пересчитываем цену если изменилось количество участников
    if "participants_count" in update_data:
        tour_price = get_tour_price(db_booking.tour_id)
        update_data["total_price"] = tour_price * update_data["participants_count"]
    
    for field, value in update_data.items():
        setattr(db_booking, field, value)
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

# PUT /bookings/{id}/cancel - отменить бронирование
@app.put("/bookings/{booking_id}/cancel", response_model=BookingSchema)
async def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking already cancelled")
    
    if db_booking.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed booking")
    
    db_booking.status = "cancelled"
    db_booking.payment_status = "refunded"
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

# POST /bookings/{id}/confirm - подтвердить бронирование
@app.post("/bookings/{booking_id}/confirm", response_model=BookingSchema)
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending bookings can be confirmed")
    
    db_booking.status = "confirmed"
    db_booking.payment_status = "paid"
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

# GET /bookings/stats - статистика бронирований
@app.get("/bookings/stats", response_model=BookingStats)
async def get_booking_stats(db: Session = Depends(get_db)):
    total_bookings = db.query(BookingModel).count()
    
    pending_bookings = db.query(BookingModel).filter(BookingModel.status == "pending").count()
    confirmed_bookings = db.query(BookingModel).filter(BookingModel.status == "confirmed").count()
    cancelled_bookings = db.query(BookingModel).filter(BookingModel.status == "cancelled").count()
    completed_bookings = db.query(BookingModel).filter(BookingModel.status == "completed").count()
    
    # Подсчет общей выручки
    revenue_result = db.query(BookingModel.total_price).filter(
        BookingModel.status.in_(["confirmed", "completed"])
    ).all()
    total_revenue = sum(Decimal(str(row[0])) for row in revenue_result)
    
    average_booking_value = total_revenue / confirmed_bookings if confirmed_bookings > 0 else Decimal("0")
    
    return BookingStats(
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        confirmed_bookings=confirmed_bookings,
        cancelled_bookings=cancelled_bookings,
        completed_bookings=completed_bookings,
        total_revenue=total_revenue,
        average_booking_value=average_booking_value
    )

# GET /bookings - все бронирования (админ)
@app.get("/bookings", response_model=List[BookingSchema])
async def get_all_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    tour_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(BookingModel)
    
    if user_id:
        query = query.filter(BookingModel.user_id == user_id)
    
    if tour_id:
        query = query.filter(BookingModel.tour_id == tour_id)
    
    if status_filter:
        query = query.filter(BookingModel.status == status_filter)
    
    bookings = query.offset(skip).limit(limit).all()
    return bookings

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)