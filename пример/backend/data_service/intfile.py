from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, APIRouter, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import models
import schemas
import crud
from database import engine, SessionLocal
import os, csv

router = APIRouter()

def get_storage_dir():
    """Получает путь к папке storage из переменной окружения"""
    return os.getenv("STORAGE_DIR", "storage")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_data(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    os.makedirs(get_storage_dir(), exist_ok=True)
    
    file_location = os.path.join(get_storage_dir(), file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    filetype = "photo" if file.filename.endswith(".jpeg") or file.filename.endswith(".png") or file.filename.endswith(".jpg") else "csv" if file.filename.endswith(".csv") else "other"

    # Если title не указан, используем имя файла
    if title is None:
        title = file.filename
    
    metadata = schemas.FileMetadataCreate(
        filename=file.filename,
        title=title,
        description=description,
        filetype=filetype,
    )

    if filetype == "csv":
        with open(file_location, "r", encoding="utf-8", newline="") as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            if header is None:
                raise HTTPException(status_code=400, detail="Файл пустой")

    db_file = crud.create_file_metadata(db, metadata)
    return db_file

@router.get("/download/{filename}")
async def download_data(filename: str):
    file_path = os.path.join(get_storage_dir(), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(file_path)

@router.get("/files")
async def list_files(db: Session = Depends(get_db)):
    return crud.get_all_files(db)

@router.delete("/files/{filename}")
async def delete_file(filename: str, db: Session = Depends(get_db)):
    file_path = os.path.join(get_storage_dir(), filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    deleted = crud.delete_file_metadata(db, filename)
    if not deleted:
        raise HTTPException(status_code=404, detail="Файл не найден в базе данных")

    return {"detail": f"Файл {filename} удалён полностью"}
 