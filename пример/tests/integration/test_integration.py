import pytest
import requests
import time
import os
import tempfile
import shutil
from unittest.mock import patch

class TestIntegration:
    """Интеграционные тесты для всего приложения"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.base_url = "http://localhost"
        self.auth_url = f"{self.base_url}/api/auth"
        self.data_url = f"{self.base_url}/api/data"
        self.processing_url = f"{self.base_url}/api/processing"
        
        # Создаем временную папку для файлов
        self.temp_dir = tempfile.mkdtemp()
        
        # Тестовые данные
        self.test_user = {
            "username": "integration_test_user",
            "password": "integration_test_pass123"
        }
        
        self.test_csv_content = """name,age,salary,city
        John,25,50000,New York
        Jane,30,60000,London
        Bob,35,70000,Paris
        Alice,28,55000,Berlin
        Charlie,32,65000,Tokyo"""
        
        # Ждем, пока сервисы запустятся
        self.wait_for_services()
    
    def wait_for_services(self):
        """Ждем, пока все сервисы запустятся"""
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Проверяем nginx
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"Services are ready after {attempt + 1} attempts")
                    return
            except requests.exceptions.RequestException:
                pass
            
            attempt += 1
            time.sleep(2)
            print(f"⏳ Waiting for services... attempt {attempt}/{max_attempts}")
        
        raise Exception("Services did not start within 60 seconds")
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        # Удаляем временную папку
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_user_lifecycle(self):
        """Полный жизненный цикл пользователя: регистрация -> вход -> проверка сессии -> выход"""
        # 1. Регистрация пользователя
        register_response = requests.post(
            f"{self.auth_url}/register",
            json=self.test_user
        )
        assert register_response.status_code == 200
        assert register_response.json()["username"] == self.test_user["username"]
        
        # 2. Вход пользователя
        login_response = requests.post(
            f"{self.auth_url}/login",
            json=self.test_user
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["token_type"] == "Bearer"
        
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Проверка сессии
        session_response = requests.get(
            f"{self.auth_url}/check-session",
            headers=headers
        )
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert "user_id" in session_data
        assert "username" in session_data
        assert session_data["username"] == self.test_user["username"]
        
        # 4. Выход пользователя
        logout_response = requests.post(f"{self.auth_url}/logout")
        assert logout_response.status_code == 200
        assert "Logged out" in logout_response.json()["message"]
    
    def test_file_upload_and_management(self):
        """Полный жизненный цикл файла: загрузка -> просмотр -> скачивание -> удаление"""
        # 1. Загружаем файл
        files = {"file": ("test_integration.csv", self.test_csv_content, "text/csv")}
        data = {"title": "Integration Test File", "description": "Test file for integration testing"}
        
        upload_response = requests.post(
            f"{self.data_url}/upload",
            files=files,
            data=data
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["filename"] == "test_integration.csv"
        assert upload_data["title"] == "Integration Test File"
        assert upload_data["filetype"] == "csv"
        
        # 2. Получаем список файлов
        list_response = requests.get(f"{self.data_url}/files")
        assert list_response.status_code == 200
        files_list = list_response.json()
        assert len(files_list) > 0
        assert any(f["filename"] == "test_integration.csv" for f in files_list)
        
        # 3. Скачиваем файл
        download_response = requests.get(f"{self.data_url}/download/test_integration.csv")
        assert download_response.status_code == 200
        assert download_response.content.decode() == self.test_csv_content
        
        # 4. Удаляем файл
        delete_response = requests.delete(f"{self.data_url}/files/test_integration.csv")
        assert delete_response.status_code == 200
        assert "удалён полностью" in delete_response.json()["detail"]
        
        # 5. Проверяем что файл удален
        final_list_response = requests.get(f"{self.data_url}/files")
        assert final_list_response.status_code == 200
        final_files_list = final_list_response.json()
        assert not any(f["filename"] == "test_integration.csv" for f in final_files_list)
    
    def test_csv_analysis_workflow(self):
        """Полный рабочий процесс анализа CSV файла"""
        # 1. Загружаем CSV файл
        files = {"file": ("analysis_test.csv", self.test_csv_content, "text/csv")}
        data = {"title": "Analysis Test File"}
        
        upload_response = requests.post(
            f"{self.data_url}/upload",
            files=files,
            data=data
        )
        assert upload_response.status_code == 200
        
        # 2. Анализируем все столбцы
        analysis_response = requests.get(f"{self.processing_url}/analyze/analysis_test.csv")
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        
        assert analysis_data["filename"] == "analysis_test.csv"
        assert analysis_data["columns_total"] == 4
        assert analysis_data["columns_selected"] == "Все"
        assert len(analysis_data["analysis"]) == 4
        
        # Проверяем статистику для числовых столбцов
        age_col = next(col for col in analysis_data["analysis"] if col["column"] == "age")
        assert age_col["sum"] == 150
        assert age_col["average"] == 30.0
        assert age_col["max"] == 35
        
        salary_col = next(col for col in analysis_data["analysis"] if col["column"] == "salary")
        assert salary_col["sum"] == 300000
        assert salary_col["average"] == 60000.0
        assert salary_col["max"] == 70000
        
        # 3. Анализируем конкретные столбцы
        specific_analysis_response = requests.get(
            f"{self.processing_url}/analyze/analysis_test.csv?columns=2,3"
        )
        assert specific_analysis_response.status_code == 200
        specific_data = specific_analysis_response.json()
        
        assert specific_data["columns_selected"] == ['age', 'salary']
        assert len(specific_data["analysis"]) == 2
        
        analyzed_columns = [col["column"] for col in specific_data["analysis"]]
        assert "age" in analyzed_columns
        assert "salary" in analyzed_columns
        assert "name" not in analyzed_columns
        assert "city" not in analyzed_columns
        
        # 4. Проверяем превью
        assert "preview" in analysis_data
        assert isinstance(analysis_data["preview"], str)
        assert len(analysis_data["preview"]) > 0
        assert "name" in analysis_data["preview"]
        assert "age" in analysis_data["preview"]
        
        # 5. Удаляем тестовый файл
        delete_response = requests.delete(f"{self.data_url}/files/analysis_test.csv")
        assert delete_response.status_code == 200
    
    def test_error_handling_integration(self):
        """Тестирование обработки ошибок в интеграции"""
        # 1. Попытка входа с неверными учетными данными
        invalid_login_response = requests.post(
            f"{self.auth_url}/login",
            json={"username": "nonexistent", "password": "wrongpass"}
        )
        assert invalid_login_response.status_code == 401
        assert "Invalid credentials" in invalid_login_response.json()["detail"]
        
        # 2. Попытка скачать несуществующий файл
        download_response = requests.get(f"{self.data_url}/download/nonexistent.csv")
        assert download_response.status_code == 404
        assert "Файл не найден" in download_response.json()["detail"]
        
        # 3. Попытка удалить несуществующий файл
        delete_response = requests.delete(f"{self.data_url}/files/nonexistent.csv")
        assert delete_response.status_code == 404
        assert "Файл не найден в базе данных" in delete_response.json()["detail"]
        
        # 4. Попытка анализа несуществующего файла
        analysis_response = requests.get(f"{self.processing_url}/analyze/nonexistent.csv")
        assert analysis_response.status_code == 404
        assert "Файл не найден" in analysis_response.json()["detail"]
    
    def test_multiple_file_types(self):
        """Тестирование работы с разными типами файлов"""
        # 1. Загружаем CSV файл
        csv_files = {"file": ("test.csv", self.test_csv_content, "text/csv")}
        csv_data = {"title": "CSV Test File"}
        
        csv_upload_response = requests.post(
            f"{self.data_url}/upload",
            files=csv_files,
            data=csv_data
        )
        assert csv_upload_response.status_code == 200
        csv_upload_data = csv_upload_response.json()
        assert csv_upload_data["filetype"] == "csv"
        
        # 2. Загружаем изображение (заглушка)
        image_content = b"fake_image_content"
        image_files = {"file": ("test.jpg", image_content, "image/jpeg")}
        image_data = {"title": "Image Test File"}
        
        image_upload_response = requests.post(
            f"{self.data_url}/upload",
            files=image_files,
            data=image_data
        )
        assert image_upload_response.status_code == 200
        image_upload_data = image_upload_response.json()
        assert image_upload_data["filetype"] == "photo"
        
        # 3. Загружаем текстовый файл
        text_content = "This is a text file content"
        text_files = {"file": ("test.txt", text_content, "text/plain")}
        text_data = {"title": "Text Test File"}
        
        text_upload_response = requests.post(
            f"{self.data_url}/upload",
            files=text_files,
            data=text_data
        )
        assert text_upload_response.status_code == 200
        text_upload_data = text_upload_response.json()
        assert text_upload_data["filetype"] == "other"
        
        # 4. Проверяем что все файлы в списке
        list_response = requests.get(f"{self.data_url}/files")
        assert list_response.status_code == 200
        files_list = list_response.json()
        
        assert any(f["filename"] == "test.csv" for f in files_list)
        assert any(f["filename"] == "test.jpg" for f in files_list)
        assert any(f["filename"] == "test.txt" for f in files_list)
        
        # 5. Очищаем тестовые файлы
        requests.delete(f"{self.data_url}/files/test.csv")
        requests.delete(f"{self.data_url}/files/test.jpg")
        requests.delete(f"{self.data_url}/files/test.txt")
    
    def test_concurrent_operations(self):
        """Тестирование параллельных операций"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def upload_file(file_num):
            """Функция для загрузки файла"""
            try:
                files = {"file": (f"concurrent_test_{file_num}.csv", self.test_csv_content, "text/csv")}
                data = {"title": f"Concurrent Test File {file_num}"}
                
                response = requests.post(
                    f"{self.data_url}/upload",
                    files=files,
                    data=data
                )
                results.put(("upload", file_num, response.status_code))
            except Exception as e:
                results.put(("upload", file_num, str(e)))
        
        def list_files():
            """Функция для получения списка файлов"""
            try:
                response = requests.get(f"{self.data_url}/files")
                results.put(("list", response.status_code))
            except Exception as e:
                results.put(("list", str(e)))
        
        # Запускаем параллельные операции
        threads = []
        for i in range(3):
            thread = threading.Thread(target=upload_file, args=(i,))
            threads.append(thread)
            thread.start()
        
        list_thread = threading.Thread(target=list_files)
        threads.append(list_thread)
        list_thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        upload_results = []
        list_result = None
        
        while not results.empty():
            result = results.get()
            if result[0] == "upload":
                upload_results.append(result)
            elif result[0] == "list":
                list_result = result
        
        # Все загрузки должны быть успешными
        assert len(upload_results) == 3
        for result in upload_results:
            assert result[2] == 200
        
        # Список файлов должен быть получен успешно
        assert list_result[1] == 200
        
        # Очищаем тестовые файлы
        for i in range(3):
            requests.delete(f"{self.data_url}/files/concurrent_test_{i}.csv")
    
    def test_health_checks(self):
        """Тестирование проверки здоровья всех сервисов"""
        # Проверяем здоровье auth-service
        auth_health_response = requests.get(f"{self.auth_url}/health")
        assert auth_health_response.status_code == 200
        auth_health_data = auth_health_response.json()
        assert auth_health_data["status"] == "healthy"
        assert auth_health_data["service"] == "auth-service"
        
        # Проверяем здоровье data-service
        data_health_response = requests.get(f"{self.data_url}/health")
        assert data_health_response.status_code == 200
        data_health_data = data_health_response.json()
        assert data_health_data["status"] == "healthy"
        assert data_health_data["service"] == "data-service"
        
        # Проверяем здоровье processing-service
        processing_health_response = requests.get(f"{self.processing_url}/health")
        assert processing_health_response.status_code == 200
        processing_health_data = processing_health_response.json()
        assert processing_health_data["status"] == "healthy"
        assert processing_health_data["service"] == "processing-service"
    
    def test_data_persistence(self):
        """Тестирование сохранения данных между запросами"""
        # 1. Загружаем файл
        files = {"file": ("persistence_test.csv", self.test_csv_content, "text/csv")}
        data = {"title": "Persistence Test File", "description": "Test for data persistence"}
        
        upload_response = requests.post(
            f"{self.data_url}/upload",
            files=files,
            data=data
        )
        assert upload_response.status_code == 200
        
        # 2. Получаем список файлов
        list_response = requests.get(f"{self.data_url}/files")
        assert list_response.status_code == 200
        files_list = list_response.json()
        
        # Находим наш файл
        test_file = next(f for f in files_list if f["filename"] == "persistence_test.csv")
        assert test_file["title"] == "Persistence Test File"
        assert test_file["description"] == "Test for data persistence"
        assert test_file["filetype"] == "csv"
        
        # 3. Анализируем файл
        analysis_response = requests.get(f"{self.processing_url}/analyze/persistence_test.csv")
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        assert analysis_data["filename"] == "persistence_test.csv"
        
        # 4. Скачиваем файл
        download_response = requests.get(f"{self.data_url}/download/persistence_test.csv")
        assert download_response.status_code == 200
        assert download_response.content.decode() == self.test_csv_content
        
        # 5. Удаляем файл
        delete_response = requests.delete(f"{self.data_url}/files/persistence_test.csv")
        assert delete_response.status_code == 200
    
    def test_large_file_handling(self):
        """Тестирование обработки больших файлов"""
        # Создаем большой CSV файл
        large_csv_content = "id,name,value\n"
        for i in range(1000):
            large_csv_content += f"{i},Name{i},{i * 100}\n"
        
        # Загружаем большой файл
        files = {"file": ("large_test.csv", large_csv_content, "text/csv")}
        data = {"title": "Large Test File"}
        
        upload_response = requests.post(
            f"{self.data_url}/upload",
            files=files,
            data=data
        )
        assert upload_response.status_code == 200
        
        # Анализируем большой файл
        analysis_response = requests.get(f"{self.processing_url}/analyze/large_test.csv")
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        
        assert analysis_data["filename"] == "large_test.csv"
        assert analysis_data["columns_total"] == 3
        
        # Проверяем статистику для столбца value
        value_col = next(col for col in analysis_data["analysis"] if col["column"] == "value")
        assert value_col["sum"] == 49950000  # Сумма от 0 до 999 * 100
        assert value_col["average"] == 49950.0
        assert value_col["max"] == 99900
        
        # Удаляем большой файл
        delete_response = requests.delete(f"{self.data_url}/files/large_test.csv")
        assert delete_response.status_code == 200



if __name__ == "__main__":
    pytest.main([__file__, "-v"])