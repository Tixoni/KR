import subprocess
import time
import sys
import os

def run_command(cmd, check=True):
    """Запускает команду с обработкой ошибок"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        return False
    return True

def setup_environment():
    """Настраивает тестовое окружение"""
    print("Setting up test environment...")
    
    # Удаляем старый кластер если существует
    run_command("k3d cluster delete tourism-cluster", check=False)
    time.sleep(5)
    
    # Создаем новый кластер
    print("Creating k3d cluster...")
    if not run_command('k3d cluster create tourism-cluster -p "8080:80@loadbalancer" --api-port 6443 --wait'):
        return False
    
    # Строим базовые образы
    print("Building base images...")
    run_command("docker build -t python:3.11-slim -f - . << 'EOF'\nFROM python:3.11-slim\nRUN pip install fastapi uvicorn\nEOF", check=False)
    run_command("docker pull nginx:alpine", check=False)
    
    # Применяем манифесты
    print("Deploying to Kubernetes...")
    manifests = [
        "k8s/namespace.yaml",
        "k8s/secrets.yaml", 
        "k8s/configmap.yaml",
        "k8s/postgres.yaml"
    ]
    
    for manifest in manifests:
        if not run_command(f"kubectl apply -f {manifest} --validate=false"):
            return False
    
    # Ждем PostgreSQL
    print("Waiting for PostgreSQL...")
    time.sleep(30)
    
    # Запускаем сервисы
    other_manifests = [
        "k8s/services-backend.yaml",
        "k8s/gateway.yaml", 
        "k8s/frontend.yaml"
    ]
    
    for manifest in other_manifests:
        run_command(f"kubectl apply -f {manifest} --validate=false")
    
    print("Setup completed. Services are starting...")
    return True

def wait_for_services():
    """Ожидает запуска сервисов"""
    print("Waiting for services to be ready...")
    
    # Ждем поды
    for i in range(30):
        result = subprocess.run(
            "kubectl get pods -n tourism -o jsonpath='{.items[*].status.phase}'",
            shell=True, capture_output=True, text=True
        )
        if "Running" in result.stdout:
            print("Services are running")
            return True
        time.sleep(10)
    
    print("Services not ready after 300 seconds")
    return False

def cleanup_environment():
    """Очищает окружение"""
    print("Cleaning up...")
    run_command("k3d cluster delete tourism-cluster", check=False)
    print("Cleanup completed")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_environment()
    elif len(sys.argv) > 1 and sys.argv[1] == "wait":
        success = wait_for_services()
        sys.exit(0 if success else 1)
    else:
        success = setup_environment()
        if success:
            success = wait_for_services()
        sys.exit(0 if success else 1)