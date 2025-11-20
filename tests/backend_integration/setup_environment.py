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

def setup_environment():
    print("Setting up test environment...")
    
    if not run_command("k3d --version"):
        print("Installing k3d...")
        run_command("curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash")
    
    print("Creating k3d cluster...")
    if not run_command('k3d cluster create tourism-cluster -p "8080:80@loadbalancer" --api-port 6443 --wait'):
        return False
    
    print("Building and importing Docker images...")
    services = ["auth-service", "tours-service", "booking-service", "frontend", "gateway"]
    
    for service in services:
        print(f"Processing {service}...")
        run_command(f"docker build -t tourism-platform-{service}:latest {service}/ || true")
        run_command(f"k3d image import tourism-platform-{service}:latest -c tourism-cluster || true")
    
    print("Deploying to Kubernetes...")
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
        run_command(f"kubectl apply -f {manifest} --validate=false")
    
    print("Waiting for services to start...")
    time.sleep(60)
    
    print("Setup completed")
    return True

def cleanup_environment():
    print("Cleaning up test environment...")
    run_command("k3d cluster delete tourism-cluster", check=False)
    print("Environment cleaned up")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_environment()
    else:
        success = setup_environment()
        sys.exit(0 if success else 1)