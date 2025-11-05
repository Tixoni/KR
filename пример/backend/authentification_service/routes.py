from fastapi import APIRouter, Depends, HTTPException, Body, Header
from sqlalchemy.orm import Session
from database import SessionLocal
import models, utils
from pydantic import BaseModel
import os, time, jwt

class UserModel(BaseModel):
    username: str
    password: str


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
async def register(user: UserModel, db: Session = Depends(get_db)):

    if db.query(models.User).filter_by(username=user.username).first():
        raise HTTPException(status_code=400, detail="User already exists")
    
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")

    user_obj = models.User(
        username=user.username, 
        password_hash=utils.hash_password(user.password)
    )

    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return {"username": user.username}

@router.post("/login")
async def login(user: UserModel, db: Session = Depends(get_db)):

    db_user = db.query(models.User).filter_by(username=user.username).first()
    if not db_user or not utils.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    jwt_secret = os.getenv("JWT_SECRET", "myjwtsecret")
    jwt_algorithm = "HS256"
    expires_in_seconds = int(os.getenv("JWT_EXPIRES_IN", "3600"))
    payload = {
        "sub": str(db_user.id),
        "username": db_user.username,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds
    }
    token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
    return {"message": "Login successful", "access_token": token, "token_type": "Bearer", "expires_in": expires_in_seconds}

@router.post("/logout")
async def logout():
    return {"message": "Logged out"}

@router.get("/check-session")
async def check_session(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    jwt_secret = os.getenv("JWT_SECRET", "myjwtsecret")
    jwt_algorithm = "HS256"
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        return {"user_id": int(payload.get("sub")), "username": payload.get("username")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
