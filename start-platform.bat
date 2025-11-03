@echo off
chcp 65001 >nul
echo Starting Tourism Platform...

echo 1. Applying Kubernetes manifests...
kubectl apply -f k8s/namespace.yaml --validate=false
kubectl apply -f k8s/secrets.yaml --validate=false
kubectl apply -f k8s/configmap.yaml --validate=false
kubectl apply -f k8s/postgres.yaml --validate=false

echo 2. Waiting for database to be ready...
timeout /t 25 /nobreak >nul

echo 3. Starting backend services...
kubectl apply -f k8s/services-backend.yaml --validate=false

echo 4. Starting gateway...
kubectl apply -f k8s/gateway.yaml --validate=false

echo 5. Starting frontend...
kubectl apply -f k8s/frontend.yaml --validate=false

echo 6. Waiting for services to be ready...
timeout /t 30 /nobreak >nul

echo 7. Checking deployment status...
kubectl get pods -n tourism

echo 8. Starting port forwarding...
start "Frontend Port Forward" kubectl port-forward -n tourism service/frontend 8081:80
timeout /t 2 /nobreak >nul
start "Gateway Port Forward" kubectl port-forward -n tourism service/gateway 8080:8080
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo Tourism Platform Started Successfully!
echo ========================================
echo.
echo 🌐 Frontend:    http://localhost:8081
echo 🌉 Gateway API: http://localhost:8080/api/auth/health
echo.
echo Port forwarding is running in background windows
echo.
echo Press any key to stop port forwarding and exit...
pause >nul

echo Stopping port forwarding...
taskkill /f /fi "windowtitle eq Frontend Port Forward*" >nul 2>&1
taskkill /f /fi "windowtitle eq Gateway Port Forward*" >nul 2>&1
taskkill /f /im kubectl.exe >nul 2>&1
echo Platform stopped.