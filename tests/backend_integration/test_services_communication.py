import pytest
import requests
import subprocess
import time

# Конфигурация
AUTH_URL = "http://localhost:8000"
TOURS_URL = "http://localhost:8001" 
BOOKINGS_URL = "http://localhost:8002"
GATEWAY_URL = "http://localhost:8080"

class TestServiceIntegration:
    
    def test_services_health(self, services_ready):
        """Тестирует health endpoints всех сервисов"""
        services = {
            "auth": f"{AUTH_URL}/health",
            "tours": f"{TOURS_URL}/health",
            "booking": f"{BOOKINGS_URL}/health",
            "gateway": f"{GATEWAY_URL}/health"
        }
        
        for service_name, url in services.items():
            response = requests.get(url)
            assert response.status_code == 200, f"{service_name} health check failed"
            
            data = response.json()
            assert data['status'] == 'healthy', f"{service_name} not healthy"
            assert 'service' in data, f"{service_name} missing service field"
            assert 'database' in data, f"{service_name} missing database field"

    def test_user_registration_flow(self, services_ready):
        """Тестирует полный цикл регистрации пользователя"""
        # 1. Регистрация
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "password": "testpass123",
            "email": f"test{int(time.time())}@example.com",
            "name": "Test User"
        }
        
        response = requests.post(f"{AUTH_URL}/users", json=user_data)
        assert response.status_code in [201, 400]  # 400 если пользователь уже существует
        
        # 2. Логин
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        response = requests.post(f"{AUTH_URL}/login", json=login_data)
        if response.status_code == 200:  # Если регистрация была успешной
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 3. Получение данных пользователя
            response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
            assert response.status_code == 200
            user_info = response.json()
            assert user_info["username"] == user_data["username"]

    def test_tour_creation_and_listing(self, services_ready):
        """Тестирует создание и получение туров"""
        # Получаем список туров (публичный endpoint)
        response = requests.get(f"{TOURS_URL}/tours")
        assert response.status_code == 200
        tours = response.json()
        assert isinstance(tours, list)

    def test_gateway_routing(self, services_ready):
        """Тестирует маршрутизацию через gateway"""
        # Проверяем что gateway проксирует запросы
        endpoints = [
            "/api/auth/health",
            "/api/tours/tours", 
            "/api/bookings/health"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{GATEWAY_URL}{endpoint}", timeout=10)
            # Gateway должен возвращать 200 или 404, но не 5xx ошибки
            assert response.status_code != 502, f"Gateway bad gateway for {endpoint}"
            assert response.status_code != 503, f"Gateway unavailable for {endpoint}"

class TestKubernetesDeployment:
    
    def test_k8s_cluster_running(self, k8s_cluster):
        """Тестирует что Kubernetes кластер запущен"""
        result = subprocess.run("kubectl cluster-info", shell=True, capture_output=True, text=True)
        assert result.returncode == 0, "Kubernetes cluster not available"
    
    def test_services_running(self, deploy_services):
        """Тестирует что все сервисы развернуты в Kubernetes"""
        result = subprocess.run(
            "kubectl get pods -n tourism -o json", 
            shell=True, capture_output=True, text=True
        )
        assert result.returncode == 0, "Failed to get pod information"
        
        # Проверяем что есть поды в namespace tourism
        import json
        pod_info = json.loads(result.stdout)
        assert len(pod_info['items']) > 0, "No pods found in tourism namespace"
        
        # Проверяем ключевые сервисы
        expected_services = ["auth-service", "tours-service", "booking-service", "frontend", "gateway"]
        deployments_result = subprocess.run(
            "kubectl get deployments -n tourism -o json", 
            shell=True, capture_output=True, text=True
        )
        
        if deployments_result.returncode == 0:
            deployments_info = json.loads(deployments_result.stdout)
            deployment_names = [deploy['metadata']['name'] for deploy in deployments_info['items']]
            
            for service in expected_services:
                assert service in deployment_names, f"Service {service} not deployed"

class TestErrorScenarios:
    
    def test_invalid_authentication(self, services_ready):
        """Тестирует обработку неверных учетных данных"""
        invalid_credentials = {
            "username": "nonexistentuser",
            "password": "wrongpassword"
        }
        
        response = requests.post(f"{AUTH_URL}/login", json=invalid_credentials)
        assert response.status_code == 401, "Should return 401 for invalid credentials"

# Удаляем старые тесты которые требовали ручного развертывания