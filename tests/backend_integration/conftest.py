import pytest
import subprocess
import time
import requests
import os
from kubernetes import client, config

@pytest.fixture(scope="session")
def k8s_cluster():
    """Разворачивает k3d кластер и устанавливает контекст"""
    print("🔄 Setting up k3d cluster...")
    
    # Проверяем, существует ли кластер
    result = subprocess.run(
        "k3d cluster list -o json", 
        shell=True, 
        capture_output=True, 
        text=True
    )
    
    cluster_exists = False
    if result.returncode == 0:
        try:
            import json
            clusters = json.loads(result.stdout)
            cluster_exists = any(cluster['name'] == 'test-tourism-cluster' for cluster in clusters)
        except:
            pass
    
    # Создаем кластер если не существует
    if not cluster_exists:
        print("📦 Creating k3d cluster...")
        create_cmd = """
        k3d cluster create test-tourism-cluster \
            --agents 1 \
            --api-port 6446 \
            --wait \
            --timeout 300s
        """
        result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            pytest.fail(f"Failed to create k3d cluster: {result.stderr}")
    
    # Устанавливаем контекст
    subprocess.run("k3d kubeconfig get test-tourism-cluster", shell=True, check=True)
    subprocess.run("kubectl config use-context k3d-test-tourism-cluster", shell=True, check=True)
    
    # Ждем готовности кластера
    print("⏳ Waiting for cluster to be ready...")
    for i in range(30):
        result = subprocess.run("kubectl get nodes", shell=True, capture_output=True)
        if result.returncode == 0:
            break
        time.sleep(2)
    else:
        pytest.fail("Kubernetes cluster not ready after 60 seconds")
    
    yield
    
    # Очистка (опционально)
    print("🧹 Cleaning up k3d cluster...")
    subprocess.run("k3d cluster delete test-tourism-cluster", shell=True, capture_output=True)

@pytest.fixture(scope="session")
def deploy_services(k8s_cluster):
    """Разворачивает сервисы Tourism Platform в кластере"""
    print("🚀 Deploying services to Kubernetes...")
    
    # Применяем манифесты
    manifests = [
        "k8s/namespace.yaml",
        "k8s/secrets.yaml", 
        "k8s/configmap.yaml",
        "k8s/postgres.yaml",
        "k8s/services-backend.yaml",
        "k8s/gateway.yaml",
        "k8s/frontend.yaml"
    ]
    
    for manifest in manifests:
        if os.path.exists(manifest):
            result = subprocess.run(f"kubectl apply -f {manifest}", shell=True, capture_output=True)
            if result.returncode != 0:
                pytest.fail(f"Failed to apply {manifest}: {result.stderr}")
    
    # Ждем готовности подов
    print("⏳ Waiting for pods to be ready...")
    deployments = ["auth-service", "tours-service", "booking-service", "frontend", "gateway"]
    
    for deployment in deployments:
        cmd = f"kubectl wait --for=condition=available --timeout=300s deployment/{deployment} -n tourism"
        result = subprocess.run(cmd, shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"⚠️ Deployment {deployment} not ready: {result.stderr}")
    
    # Ждем PostgreSQL
    subprocess.run(
        "kubectl wait --for=condition=ready --timeout=300s pod -l app=postgres -n tourism",
        shell=True, capture_output=True
    )
    
    # Запускаем port-forward
    print("🔗 Starting port forwarding...")
    port_forward_commands = [
        "kubectl port-forward -n tourism deployment/auth-service 8000:8000 > /dev/null 2>&1 &",
        "kubectl port-forward -n tourism deployment/tours-service 8001:8001 > /dev/null 2>&1 &", 
        "kubectl port-forward -n tourism deployment/booking-service 8002:8002 > /dev/null 2>&1 &",
        "kubectl port-forward -n tourism service/gateway 8080:8080 > /dev/null 2>&1 &"
    ]
    
    for cmd in port_forward_commands:
        subprocess.run(cmd, shell=True)
    
    # Даем время для запуска port-forward
    time.sleep(10)
    
    yield
    
    # Останавливаем port-forward
    print("🛑 Stopping port forwarding...")
    subprocess.run("pkill -f 'kubectl port-forward'", shell=True, capture_output=True)

@pytest.fixture(scope="session")
def services_ready(deploy_services):
    """Ожидает готовности всех сервисов"""
    print("🔍 Checking service readiness...")
    
    services = [
        "http://localhost:8000/health",
        "http://localhost:8001/health", 
        "http://localhost:8002/health",
        "http://localhost:8080/health"
    ]
    
    def wait_for_service(url, timeout=120):
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        return True
            except:
                pass
            time.sleep(2)
        return False
    
    for service_url in services:
        print(f"Waiting for {service_url}...")
        if not wait_for_service(service_url):
            pytest.fail(f"Service not ready: {service_url}")
    
    print("✅ All services are ready!")