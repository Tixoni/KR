from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from fastapi import Request
from fastapi.responses import JSONResponse
from intfile import router
import models
from database import engine
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
    yield
    print("Application shutdown")

app = FastAPI(title="Data Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 1024 * 1024 * 1024 * 2

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > MAX_FILE_SIZE:
        return JSONResponse(content={"detail": "File too large"}, status_code=413)
    return await call_next(request)

app.include_router(router, prefix="", tags=["data"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "data-service"}