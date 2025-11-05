import pytest
import os
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

# Добавляем родительский каталог в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import json

from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_csv_content():
    """Пример содержимого CSV файла"""
    return """name,age,salary,city
    John,25,50000,New York
    Jane,30,60000,London
    Bob,35,70000,Paris
    Alice,28,55000,Berlin
    Charlie,32,65000,Tokyo"""

@pytest.fixture
def sample_csv_file(temp_storage, sample_csv_content):
    """Создает тестовый CSV файл"""
    filename = "test_data.csv"
    filepath = os.path.join(temp_storage, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(sample_csv_content)
    
    return filename, filepath

@pytest.fixture
def temp_storage():
    """Временная папка для хранения файлов"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

class TestCSVAnalysis:
    """Тесты анализа CSV файлов"""
    
    def test_analyze_csv_all_columns(self, client, sample_csv_file, temp_storage):
        """Анализ всех столбцов CSV файла"""
        filename, filepath = sample_csv_file
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["filename"] == filename
        assert data["columns_total"] == 4
        assert data["columns_selected"] == "Все"
        assert len(data["analysis"]) == 4
        
        numeric_columns = [col for col in data["analysis"] if col["column"] in ["age", "salary"]]
        assert len(numeric_columns) == 2
        
        age_stats = next(col for col in data["analysis"] if col["column"] == "age")
        assert age_stats["sum"] == 150
        assert age_stats["average"] == 30.0
        assert age_stats["max"] == 35
    
    def test_analyze_csv_specific_columns(self, client, sample_csv_file, temp_storage):
        """Анализ конкретных столбцов CSV файла"""
        filename, filepath = sample_csv_file
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}?columns=2,3")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns_selected"] == ['age', 'salary']
        assert len(data["analysis"]) == 2
        
        analyzed_columns = [col["column"] for col in data["analysis"]]
        assert "age" in analyzed_columns
        assert "salary" in analyzed_columns
        assert "name" not in analyzed_columns
        assert "city" not in analyzed_columns
    
    def test_analyze_csv_single_column(self, client, sample_csv_file, temp_storage):
        """Анализ одного столбца"""
        filename, filepath = sample_csv_file
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}?columns=3")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns_selected"] == ['salary']
        assert len(data["analysis"]) == 1
        assert data["analysis"][0]["column"] == "salary"
        assert data["analysis"][0]["sum"] == 300000
    
    def test_analyze_csv_nonexistent_file(self, client, temp_storage):
        """Анализ несуществующего файла"""
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get("/analyze/nonexistent.csv")
            
        assert response.status_code == 404
        assert "Файл не найден" in response.json()["detail"]
    
    def test_analyze_csv_invalid_columns(self, client, sample_csv_file, temp_storage):
        """Анализ с неверными номерами столбцов"""
        filename, filepath = sample_csv_file
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}?columns=10,20")
            
        assert response.status_code == 400
        assert "Некорректный номер столбца" in response.json()["detail"]
    
    def test_analyze_csv_non_numeric_columns(self, client, temp_storage):
        """Анализ файла только с текстовыми столбцами"""
        filename = "text_only.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = """name,city,country
        John,New York,USA
        Jane,London,UK
        Bob,Paris,France"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns_total"] == 3
        assert len(data["analysis"]) == 3
        
        for col in data["analysis"]:
            assert col["sum"] == "невозможно определить"
            assert col["average"] == "невозможно определить"
            assert col["max"] == "невозможно определить"
    
    def test_analyze_csv_mixed_data_types(self, client, temp_storage):
        """Анализ файла со смешанными типами данных"""
        filename = "mixed_data.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = """id,name,score,active
        1,John,85.5,true
        2,Jane,92.0,false
        3,Bob,78.3,true"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        score_col = next(col for col in data["analysis"] if col["column"] == "score")
        assert score_col["sum"] == 255.8
        assert score_col["average"] == 85.27
        assert score_col["max"] == 92.0

class TestCSVPreview:
    """Тесты предварительного просмотра CSV"""
    
    def test_preview_csv_content(self, client, sample_csv_file, temp_storage):
        """Получение превью CSV файла"""
        filename, filepath = sample_csv_file
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        assert "preview" in data
        assert isinstance(data["preview"], str)
        assert len(data["preview"]) > 0
        
        assert "name" in data["preview"]
        assert "age" in data["preview"]
        assert "salary" in data["preview"]
        assert "city" in data["preview"]

class TestErrorHandling:
    """Тесты обработки ошибок"""

    def test_analyze_empty_csv(self, client, temp_storage):
        """Анализ пустого CSV файла"""
        filename = "empty.csv"
        filepath = os.path.join(temp_storage, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("")
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 400
        assert "Файл пустой" in response.json()["detail"]
    
    def test_analyze_corrupted_csv(self, client, temp_storage):
        """Анализ поврежденного CSV файла"""
        filename = "corrupted.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = "name,age\nJohn,25\nJane,30\nBob"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code in [200, 500]
    
    def test_analyze_non_csv_file(self, client, temp_storage):
        """Анализ файла, который не является CSV"""
        filename = "not_csv.txt"
        filepath = os.path.join(temp_storage, filename)
        
        content = "This is not a CSV file\nIt has multiple lines\nBut no comma separation"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code in [200, 500]
    
    def test_analyze_file_with_special_characters(self, client, temp_storage):
        """Анализ файла со специальными символами"""
        filename = "special_chars.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = """name,description,value
        John,Contains special characters,100
        Jane,l_o_l,200
        Bob,k.e.k,300"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns_total"] == 3
        assert len(data["analysis"]) == 3
        
        value_col = next(col for col in data["analysis"] if col["column"] == "value")
        assert value_col["sum"] == 600
        assert value_col["average"] == 200.0

class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_analyze_csv_with_only_headers(self, client, temp_storage):
        """Анализ CSV файла только с заголовками"""
        filename = "headers_only.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = "name,age,salary"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns_total"] == 3
        assert len(data["analysis"]) == 3
        
        for col in data["analysis"]:
            assert col["sum"] == 0
            assert col["average"] == "невозможно определить"
            assert col["max"] == "невозможно определить"
    
    def test_analyze_csv_with_single_row(self, client, temp_storage):
        """Анализ CSV файла с одной строкой данных"""
        filename = "single_row.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = """name,age,salary
John,25,50000"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns_total"] == 3
        assert len(data["analysis"]) == 3
        
        age_col = next(col for col in data["analysis"] if col["column"] == "age")
        assert age_col["sum"] == 25
        assert age_col["average"] == 25.0
        assert age_col["max"] == 25
    
    def test_analyze_csv_with_very_large_numbers(self, client, temp_storage):
        """Анализ CSV файла с очень большими числами"""
        filename = "large_numbers.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = """id,value
        1,999999999999999
        2,1000000000000000
        3,2000000000000000"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        value_col = next(col for col in data["analysis"] if col["column"] == "value")
        assert value_col["sum"] == 3999999999999999
        assert value_col["average"] == 1333333333333333.0
        assert value_col["max"] == 2000000000000000

class TestPerformance:
    """Тесты производительности"""
    
    def test_analyze_large_csv(self, client, temp_storage):
        """Анализ большого CSV файла"""
        filename = "large.csv"
        filepath = os.path.join(temp_storage, filename)
        
        content = "id,name,value\n"
        for i in range(1000):
            content += f"{i},Name{i},{i * 100}\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with patch('main.get_storage_dir', return_value=temp_storage):
            response = client.get(f"/analyze/{filename}")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns_total"] == 3
        assert len(data["analysis"]) == 3
        
        value_col = next(col for col in data["analysis"] if col["column"] == "value")
        assert value_col["sum"] == 49950000
        assert value_col["average"] == 49950.0
        assert value_col["max"] == 99900

if __name__ == "__main__":
    pytest.main([__file__, "-v"])