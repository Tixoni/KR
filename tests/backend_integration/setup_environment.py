import subprocess
import time
import sys
import os
import requests

def run_command(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        return False
    return result.returncode == 0

def wait_for_service(url, timeout=120):
    print(f"Waiting for {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"Service {url} is available")
                return True
        except requests.RequestException:
            pass
        time.sleep(5)
    print(f"Service {url} not available after {timeout} seconds")
    return False

def setup_environment():
    print("Setting up test environment...")
    
    if not run_command("docker --version"):
        print("Docker not installed")
        return False
    
    if not run_command("k3d --version"):
        print("k3d not installed")
        return False
    
    if not run_command("k3d cluster list | grep tourism-cluster", check=False):
        print("Creating k3d cluster...")
        if not run_command('k3d cluster create tourism-cluster -p "8080:80@loadbalancer" --api-port 6443 --wait'):
            return False
    
    print("Starting cluster...")
    if not run_command("k3d cluster start tourism-cluster"):
        return False
    
    print("Building Docker images...")
    services = ["auth-service", "tours-service", "booking-service", "frontend", "gateway"]
    
    for service in services:
        print(f"Building {service}...")
        if not run_command(f"docker build -t tourism-platform-{service}:latest {service}/"):
            print(f"Using fallback for {service}")
    
    print("Importing images to k3d...")
    for service in services:
        image_name = f"tourism-platform-{service}:latest"
        if not run_command(f"k3d image import {image_name} -c tourism-cluster", check=False):
            print(f"Skipping {service}")
    
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
    
    print("Waiting for PostgreSQL...")
    time.sleep(30)
    
    other_manifests = [
        "k8s/services-backend.yaml",
        "k8s/gateway.yaml", 
        "k8s/frontend.yaml"
    ]
    
    for manifest in other_manifests:
        if not run_command(f"kubectl apply -f {manifest} --validate=false"):
            return False
    
    print("Waiting for services to start...")
    time.sleep(45)
    
    print("Checking service health...")
    health_endpoints = [
        "http://localhost:8080/api/auth/health",
        "http://localhost:8080/api/tours/health", 
        "http://localhost:8080/api/bookings/health"
    ]
    
    for endpoint in health_endpoints:
        if not wait_for_service(endpoint, timeout=60):
            print(f"Service failed to start: {endpoint}")
            run_command("kubectl get pods -n tourism", check=False)
            run_command("kubectl logs -n tourism deployment/auth-service --tail=20", check=False)
            return False
    
    print("All services are ready for testing")
    return True

def cleanup_environment():
    print("Cleaning up test environment...")
    
    run_command("kubectl delete -f k8s/ --ignore-not-found=true --recursive", check=False)
    run_command("kubectl delete namespace tourism --ignore-not-found=true", check=False)
    run_command("k3d cluster stop tourism-cluster", check=False)
    
    print("Environment cleaned up")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_environment()
    else:
        success = setup_environment()
        sys.exit(0 if success else 1)