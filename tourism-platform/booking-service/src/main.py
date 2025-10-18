# booking-service/src/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import httpx
import os

# Импорты для работы в контейнере
from .models import Booking as BookingModel
from .schemas import (
    BookingCreate, BookingUpdate, BookingStatusUpdate, 
    Booking as BookingSchema, BookingStats
)
from .database import SessionLocal, engine, get_db
from .auth_utils import verify_token, validate_user_exists

# Таблицы создаются в init.sql при инициализации БД

app = FastAPI(
    title="Booking Service",
    description="Microservice for managing tour bookings",
    version="1.0.0"
)

security = HTTPBearer()

# Функция для получения текущего пользователя из токена
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = verify_token(credentials.credentials)
    if username is None:
        raise credentials_exception
    
    return username

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "booking-service"}

# Вспомогательная функция для получения цены тура
async def get_tour_price(tour_id: int) -> Decimal:
    """Получает цену тура из tours-service"""
    try:
        async with httpx.AsyncClient() as client:
            # В Docker compose используем имя сервиса
            tours_service_url = os.getenv("TOURS_SERVICE_URL", "http://tours-service:8001")
            # Эндпоинт /tours/{tour_id} не требует аутентификации, поэтому не передаем токен
            response = await client.get(f"{tours_service_url}/tours/{tour_id}")
            if response.status_code == 200:
                tour_data = response.json()
                return Decimal(str(tour_data["price"]))
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tour not found"
                )
    except httpx.RequestError as e:
        print(f"Ошибка подключения к tours-service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tours service unavailable"
        )

# POST /bookings - создать бронирование
@app.post("/bookings", response_model=BookingSchema, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking: BookingCreate, 
    current_user: str = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        print(f"Создание бронирования: user_id={booking.user_id}, tour_id={booking.tour_id}")
        
        # Проверяем существование пользователя, передавая токен
        await validate_user_exists(booking.user_id, credentials.credentials)
        print("Пользователь найден")
        
        # Получаем цену тура из tours-service
        tour_price = await get_tour_price(booking.tour_id)
        total_price = tour_price * booking.participants_count
        print(f"Цена тура: {tour_price}, общая цена: {total_price}")
        
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
        print(f"Бронирование создано с ID: {db_booking.id}")
        return db_booking
    except Exception as e:
        db.rollback()
        print(f"Ошибка создания бронирования: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating booking: {str(e)}")

# GET /bookings/{id} - получить бронирование по ID
@app.get("/bookings/{booking_id}", response_model=BookingSchema)
async def get_booking(
    booking_id: int, 
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
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
        tour_price = await get_tour_price(db_booking.tour_id)
        update_data["total_price"] = tour_price * update_data["participants_count"]
    
    for field, value in update_data.items():
        setattr(db_booking, field, value)
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

# PUT /bookings/{id}/cancel - отменить бронирование
@app.put("/bookings/{booking_id}/cancel", response_model=BookingSchema)
async def cancel_booking(
    booking_id: int, 
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
async def confirm_booking(
    booking_id: int, 
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
async def get_booking_stats(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    current_user: str = Depends(get_current_user),
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