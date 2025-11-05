import pytest
import os
import tempfile
import shutil
import sys
from pathlib import Path

# Добавляем родительский каталог в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, mock_open
import json

from main import app
from database import Base
from models import FileMetadata
import crud
import schemas

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_data.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Переопределяем engine для тестов
import database
database.engine = engine

# Переопределяем engine в main тоже
import main
main.engine = engine

# Переопределяем engine в intfile тоже
import intfile
intfile.engine = engine
intfile.SessionLocal = TestingSessionLocal

# Импортируем get_db после переопределения engine
from database import get_db

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def temp_storage():
    """Временная папка для хранения файлов"""
    temp_dir = tempfile.mkdtemp()
    original_storage = os.environ.get("STORAGE_DIR", "storage")
    
    with patch.dict(os.environ, {"STORAGE_DIR": temp_dir}):
        yield temp_dir

    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_csv_content():
    """Пример содержимого CSV файла"""
    return "name,age,city\nJohn,25,New York\nJane,30,London\nBob,35,Paris"

@pytest.fixture
def sample_image_content():
    """Пример содержимого изображения (заглушка)"""
    return b"fake_image_content"

class TestFileUpload:
    """Тесты загрузки файлов"""
    
    def test_upload_csv_file(self, client, setup_database, temp_storage, sample_csv_content):
        """Загрузка CSV файла"""
        files = {"file": ("test.csv", sample_csv_content, "text/csv")}
        data = {"title": "Test CSV", "description": "Test description"}
        
        response = client.post("/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["filename"] == "test.csv"
        assert result["title"] == "Test CSV"
        assert result["description"] == "Test description"
        assert result["filetype"] == "csv"
    
    def test_upload_image_file(self, client, setup_database, temp_storage, sample_image_content):
        """Загрузка изображения"""
        files = {"file": ("test.jpg", sample_image_content, "image/jpeg")}
        data = {"title": "Test Image", "description": "Test image description"}
        
        response = client.post("/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["filename"] == "test.jpg"
        assert result["filetype"] == "photo"

    def test_upload_empty_csv(self, client, setup_database, temp_storage):
        """Загрузка пустого CSV файла"""
        files = {"file": ("empty.csv", "", "text/csv")}
        data = {"title": "Empty CSV", "description": "Empty CSV description"}
        
        response = client.post("/upload", files=files, data=data)
        assert response.status_code == 400
        assert "Файл пустой" in response.json()["detail"]
    
    def test_upload_without_file(self, client, setup_database):
        """Попытка загрузки без файла"""
        response = client.post("/upload")
        assert response.status_code == 422
    
    def test_upload_large_file(self, client, setup_database, temp_storage):
        """Тест загрузки большого файла"""
        large_content = "x" * (1024 * 1024 * 1024 * 2 + 10)
        
        files = {"file": ("large.txt", large_content, "text/plain")}
        data = {"title": "Large File"}
        
        response = client.post("/upload", files=files, data=data)
        assert response.status_code == 413
    
    def test_upload_file_without_title(self, client, setup_database, temp_storage, sample_csv_content):
        """Загрузка файла без указания названия"""
        files = {"file": ("auto_name.csv", sample_csv_content, "text/csv")}
        data = {"description": "Auto named file"}
        
        response = client.post("/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["title"] == "auto_name.csv"
        assert result["description"] == "Auto named file"

class TestFileDownload:
    """Тесты скачивания файлов"""
    
    def test_download_existing_file(self, client, setup_database, temp_storage, sample_csv_content):
        """Скачивание существующего файла"""

        files = {"file": ("download_test.csv", sample_csv_content, "text/csv")}
        upload_response = client.post("/upload", files=files)
        filename = upload_response.json()["filename"]
        
        response = client.get(f"/download/{filename}")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert response.content.decode() == sample_csv_content
    
    def test_download_nonexistent_file(self, client, setup_database):
        """Попытка скачать несуществующий файл"""
        response = client.get("/download/nonexistent.csv")
        assert response.status_code == 404
        assert "Файл не найден" in response.json()["detail"]
    
    def test_download_file_with_special_characters(self, client, setup_database, temp_storage, sample_csv_content):
        """Скачивание файла со специальными символами в имени"""
        files = {"file": ("файл с пробелами.csv", sample_csv_content, "text/csv")}
        upload_response = client.post("/upload", files=files)
        filename = upload_response.json()["filename"]
        
        response = client.get(f"/download/{filename}")
        assert response.status_code == 200

class TestFileListing:
    """Тесты получения списка файлов"""
    
    def test_list_empty_files(self, client, setup_database):
        """Получение списка файлов когда их нет"""
        response = client.get("/files")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_files_with_data(self, client, setup_database, temp_storage, sample_csv_content):
        """Получение списка файлов с данными"""
        files1 = {"file": ("file1.csv", sample_csv_content, "text/csv")}
        files2 = {"file": ("file2.csv", sample_csv_content, "text/csv")}
        
        client.post("/upload", files=files1, data={"title": "File 1"})
        client.post("/upload", files=files2, data={"title": "File 2"})
        
        response = client.get("/files")
        assert response.status_code == 200
        
        files = response.json()
        assert len(files) == 2
        assert any(f["title"] == "File 1" for f in files)
        assert any(f["title"] == "File 2" for f in files)
    
    def test_list_files_with_metadata(self, client, setup_database, temp_storage, sample_csv_content):
        """Получение списка файлов с метаданными"""
        files = {"file": ("metadata_test.csv", sample_csv_content, "text/csv")}
        data = {
            "title": "Metadata Test",
            "description": "Test with metadata",
        }
        
        client.post("/upload", files=files, data=data)
        
        response = client.get("/files")
        assert response.status_code == 200
        
        files_list = response.json()
        assert len(files_list) == 1
        
        file_data = files_list[0]
        assert file_data["title"] == "Metadata Test"
        assert file_data["description"] == "Test with metadata"

class TestFileDeletion:
    """Тесты удаления файлов"""
    
    def test_delete_existing_file(self, client, setup_database, temp_storage, sample_csv_content):
        """Удаление существующего файла"""

        files = {"file": ("delete_test.csv", sample_csv_content, "text/csv")}
        upload_response = client.post("/upload", files=files)
        filename = upload_response.json()["filename"]
        
        response = client.delete(f"/files/{filename}")
        assert response.status_code == 200
        assert f"Файл {filename} удалён полностью" in response.json()["detail"]
        
        list_response = client.get("/files")
        files_list = list_response.json()
        assert not any(f["filename"] == filename for f in files_list)
    
    def test_delete_nonexistent_file(self, client, setup_database):
        """Попытка удалить несуществующий файл"""
        response = client.delete("/files/nonexistent.csv")
        assert response.status_code == 404
        assert "Файл не найден в базе данных" in response.json()["detail"]
    
    def test_delete_file_removes_from_storage(self, client, setup_database, temp_storage, sample_csv_content):
        """Проверка что файл удаляется из хранилища"""
        files = {"file": ("storage_test.csv", sample_csv_content, "text/csv")}
        upload_response = client.post("/upload", files=files)
        filename = upload_response.json()["filename"]
        
        file_path = os.path.join(temp_storage, filename)
        assert os.path.exists(file_path)
        
        client.delete(f"/files/{filename}")
        
        assert not os.path.exists(file_path)

class TestCRUDOperations:
    """Тесты CRUD операций"""
    
    def test_create_file_metadata(self, setup_database):
        """Создание метаданных файла"""
        db = TestingSessionLocal()
        
        file_metadata = schemas.FileMetadataCreate(
            filename="test.csv",
            filetype="csv",
            title="Test File",
            description="Test description"
        )
        
        result = crud.create_file_metadata(db, file_metadata)
        
        assert result.filename == "test.csv"
        assert result.filetype == "csv"
        assert result.title == "Test File"
        assert result.description == "Test description"
        assert result.id is not None
        
        db.close()
    
    def test_get_all_files(self, setup_database):
        """Получение всех файлов"""
        db = TestingSessionLocal()
        
        file1 = schemas.FileMetadataCreate(filename="file1.csv", filetype="csv")
        file2 = schemas.FileMetadataCreate(filename="file2.jpg", filetype="photo")
        
        crud.create_file_metadata(db, file1)
        crud.create_file_metadata(db, file2)
        
        files = crud.get_all_files(db)
        
        assert len(files) == 2
        assert any(f.filename == "file1.csv" for f in files)
        assert any(f.filename == "file2.jpg" for f in files)
        
        db.close()
    
    def test_delete_file_metadata(self, setup_database):
        """Удаление метаданных файла"""
        db = TestingSessionLocal()
        
        file_metadata = schemas.FileMetadataCreate(filename="delete_test.csv", filetype="csv")
        created_file = crud.create_file_metadata(db, file_metadata)
        
        result = crud.delete_file_metadata(db, "delete_test.csv")
        assert result == True

        files = crud.get_all_files(db)
        assert not any(f.filename == "delete_test.csv" for f in files)
        
        db.close()
    
    def test_delete_nonexistent_file_metadata(self, setup_database):
        """Удаление несуществующих метаданных"""
        db = TestingSessionLocal()
        
        result = crud.delete_file_metadata(db, "nonexistent.csv")
        assert result == False
        
        db.close()

class TestFileTypeDetection:
    """Тесты определения типа файла"""
    
    def test_csv_file_type_detection(self, client, setup_database, temp_storage, sample_csv_content):
        """Определение типа CSV файла"""
        files = {"file": ("test.csv", sample_csv_content, "text/csv")}
        response = client.post("/upload", files=files)
        
        result = response.json()
        assert result["filetype"] == "csv"
    
    def test_image_file_type_detection(self, client, setup_database, temp_storage, sample_image_content):
        """Определение типа изображения"""
        files = {"file": ("test.jpg", sample_image_content, "image/jpeg")}
        response = client.post("/upload", files=files)
        
        result = response.json()
        assert result["filetype"] == "photo"
    
    def test_png_file_type_detection(self, client, setup_database, temp_storage, sample_image_content):
        """Определение типа PNG файла"""
        files = {"file": ("test.png", sample_image_content, "image/png")}
        response = client.post("/upload", files=files)
        
        result = response.json()
        assert result["filetype"] == "photo"
    
    def test_other_file_type_detection(self, client, setup_database, temp_storage):
        """Определение типа других файлов"""
        files = {"file": ("test.txt", "some text content", "text/plain")}
        response = client.post("/upload", files=files)
        
        result = response.json()
        assert result["filetype"] == "other"

class TestHealthCheck:
    """Тесты проверки здоровья сервиса"""
    
    def test_health_check(self, client):
        """Проверка эндпоинта здоровья"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "data-service"


class TestIntegration:
    """Интеграционные тесты полного цикла"""
    
    def test_full_file_lifecycle(self, client, setup_database, temp_storage, sample_csv_content):
        """Полный жизненный цикл файла"""
        filename = "lifecycle_test.csv"
        files = {"file": (filename, sample_csv_content, "text/csv")}
        data = {"title": "Lifecycle Test", "description": "Full lifecycle test"}
        
        upload_response = client.post("/upload", files=files, data=data)
        assert upload_response.status_code == 200
        uploaded_file = upload_response.json()
        
        list_response = client.get("/files")
        files_list = list_response.json()
        assert any(f["filename"] == filename for f in files_list)
        
        download_response = client.get(f"/download/{filename}")
        assert download_response.status_code == 200
        assert download_response.content.decode() == sample_csv_content
        
        delete_response = client.delete(f"/files/{filename}")
        assert delete_response.status_code == 200
        
        final_list_response = client.get("/files")
        final_files_list = final_list_response.json()
        assert not any(f["filename"] == filename for f in final_files_list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
