@echo off
chcp 65001 >nul
echo 🚀 Tourism Platform Cluster Fixer
echo =================================
echo.

echo 1. Stopping and deleting old cluster...
k3d cluster delete tourism-cluster

echo 2. Creating new cluster with FIXED API and LB ports...
REM Map host 8080 -> LB 80 for Ingress/Services; set fixed API port; wait until ready
k3d cluster create tourism-cluster -p "8080:80@loadbalancer" --api-port 6443 --wait

echo 3. Updating kubeconfig...
k3d kubeconfig merge tourism-cluster --kubeconfig-switch-context

echo 4. Verifying connection...
kubectl cluster-info
kubectl get nodes

echo.
echo ✅ Cluster fixed and ready!
echo 🌐 Use manage-platform.bat to deploy your application
echo.
pause