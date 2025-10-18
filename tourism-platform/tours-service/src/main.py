# tours-service/src/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

# Импорты для работы в контейнере
from .models import Tour as TourModel  # Модель из models.py
from .schemas import TourCreate, TourUpdate, Tour as TourSchema  # Схемы из schemas.py
from .database import SessionLocal, engine, get_db
from .auth_utils import verify_token

# Таблицы создаются в init.sql при инициализации БД

app = FastAPI(
    title="Tours Service",
    description="Microservice for managing tours",
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
    return {"status": "healthy", "service": "tours-service"}

# Get all tours
@app.get("/tours", response_model=List[TourSchema])
async def get_tours(
    skip: int = 0, 
    limit: int = 100,
    destination: Optional[str] = None,
    available: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TourModel)
    
    if destination:
        query = query.filter(TourModel.destination.ilike(f"%{destination}%"))
    
    if available is not None:
        query = query.filter(TourModel.available == available)
    
    tours = query.offset(skip).limit(limit).all()
    return tours

# Get tour by ID
@app.get("/tours/{tour_id}", response_model=TourSchema)
async def get_tour(tour_id: int, db: Session = Depends(get_db)):
    tour = db.query(TourModel).filter(TourModel.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour

# Create new tour
@app.post("/tours", response_model=TourSchema, status_code=status.HTTP_201_CREATED)
async def create_tour(
    tour: TourCreate, 
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_tour = TourModel(
        title=tour.title,
        description=tour.description,
        destination=tour.destination,
        price=tour.price,
        duration_days=tour.duration_days,
        available=tour.available,
        features=tour.features
    )
    
    db.add(db_tour)
    db.commit()
    db.refresh(db_tour)
    return db_tour

# Update tour
@app.put("/tours/{tour_id}", response_model=TourSchema)
async def update_tour(
    tour_id: int, 
    tour_update: TourUpdate, 
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_tour = db.query(TourModel).filter(TourModel.id == tour_id).first()
    if not db_tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    update_data = tour_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tour, field, value)
    
    db.commit()
    db.refresh(db_tour)
    return db_tour

# Delete tour
@app.delete("/tours/{tour_id}")
async def delete_tour(
    tour_id: int, 
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tour = db.query(TourModel).filter(TourModel.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    db.delete(tour)
    db.commit()
    return {"message": "Tour deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)