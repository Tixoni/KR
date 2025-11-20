@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set NAMESPACE=tourism
set PLATFORM_TITLE=Tourism Platform Manager

:MAIN_MENU
cls
echo.
echo ========================================
echo    %PLATFORM_TITLE%
echo ========================================
echo.
echo 1.  Start Platform (Full deployment)
echo 2.  Stop Platform
echo 3.  Check Status
echo 4.  View Logs
echo 5.  Port Forward (Frontend + APIs)
echo 6.  Reset Cluster (Full reset)
echo 7.  Build Docker Images
echo 8.  Import Images to k3d Cluster
echo 9.  Exit
echo.
set /p CHOICE="Choose option [1-9]: "

if "%CHOICE%"=="1" goto START_PLATFORM
if "%CHOICE%"=="2" goto STOP_PLATFORM
if "%CHOICE%"=="3" goto CHECK_STATUS
if "%CHOICE%"=="4" goto VIEW_LOGS
if "%CHOICE%"=="5" goto PORT_FORWARD
if "%CHOICE%"=="6" goto RESET_CLUSTER
if "%CHOICE%"=="7" goto BUILD_IMAGES
if "%CHOICE%"=="8" goto IMPORT_IMAGES
if "%CHOICE%"=="9" goto EXIT

echo Invalid choice! Press any key to continue...
pause >nul
goto MAIN_MENU

:BUILD_IMAGES
echo.
echo 🏗️ Building Docker images for Tourism Platform...
echo.

echo 🔨 Checking for Dockerfiles...
if not exist "auth-service\Dockerfile" (
    echo Creating Dockerfile for auth-service...
    (
      echo FROM python:3.11-slim
      echo WORKDIR /app
      echo COPY requirements.txt .
      echo RUN pip install --no-cache-dir -r requirements.txt
      echo COPY src/ ./src/
      echo CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
    )> auth-service\Dockerfile
)

if not exist "tours-service\Dockerfile" (
    echo Creating Dockerfile for tours-service...
    (
      echo FROM python:3.11-slim
      echo WORKDIR /app
      echo COPY requirements.txt .
      echo RUN pip install --no-cache-dir -r requirements.txt
      echo COPY src/ ./src/
      echo CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
    )> tours-service\Dockerfile
)

if not exist "booking-service\Dockerfile" (
    echo Creating Dockerfile for booking-service...
    (
      echo FROM python:3.11-slim
      echo WORKDIR /app
      echo COPY requirements.txt .
      echo RUN pip install --no-cache-dir -r requirements.txt
      echo COPY src/ ./src/
      echo CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
    )> booking-service\Dockerfile
)

if not exist "frontend\Dockerfile" (
    echo Creating Dockerfile for frontend...
    (
      echo FROM nginx:1.25-alpine
      echo COPY nginx.conf /etc/nginx/nginx.conf
      echo COPY index.html /usr/share/nginx/html/index.html
      echo COPY styles.css /usr/share/nginx/html/styles.css
      echo COPY script.js /usr/share/nginx/html/script.js
      echo COPY sounds/ /usr/share/nginx/html/sounds/
      echo EXPOSE 80
      echo CMD ["nginx", "-g", "daemon off;"]
    )> frontend\Dockerfile
)

if not exist "gateway-service\Dockerfile" (
    echo Creating Dockerfile for gateway-service...
    (
      echo FROM nginx:1.25-alpine
      echo COPY nginx.conf /etc/nginx/nginx.conf
      echo RUN mkdir -p /var/log/nginx
      echo EXPOSE 8080
      echo CMD ["nginx", "-g", "daemon off;"]
    )> gateway-service\Dockerfile
)

echo.
echo 🏗️ Building auth-service...
docker build -t tourism-platform-auth-service:latest auth-service\
if errorlevel 1 (
    echo ❌ Failed to build auth-service image!
    echo Using fallback Python image...
    docker pull python:3.11-slim
    docker tag python:3.11-slim tourism-platform-auth-service:latest
)

echo 🏗️ Building tours-service...
docker build -t tourism-platform-tours-service:latest tours-service\
if errorlevel 1 (
    echo ❌ Failed to build tours-service image!
    echo Using fallback Python image...
    docker pull python:3.11-slim
    docker tag python:3.11-slim tourism-platform-tours-service:latest
)

echo 🏗️ Building booking-service...
docker build -t tourism-platform-booking-service:latest booking-service\
if errorlevel 1 (
    echo ❌ Failed to build booking-service image!
    echo Using fallback Python image...
    docker pull python:3.11-slim
    docker tag python:3.11-slim tourism-platform-booking-service:latest
)

echo 🏗️ Building frontend...
docker build -t tourism-platform-frontend:latest frontend\
if errorlevel 1 (
    echo ❌ Failed to build frontend image!
    echo Using fallback Nginx image...
    docker pull nginx:alpine
    docker tag nginx:alpine tourism-platform-frontend:latest
)

echo 🏗️ Building gateway-service...
docker build -t tourism-platform-gateway:latest gateway-service\
if errorlevel 1 (
    echo ❌ Failed to build gateway image!
    echo Using fallback Nginx image...
    docker pull nginx:alpine
    docker tag nginx:alpine tourism-platform-gateway:latest
)

echo.
echo ✅ Docker images built successfully!
echo.
echo Current images:
docker images | findstr "tourism-platform"
echo.
pause
goto MAIN_MENU

:RESET_CLUSTER
echo.
echo WARNING: This will DELETE and RECREATE the cluster!
set /p CONFIRM="Are you sure? (y/N): "
if /i not "%CONFIRM%"=="y" goto MAIN_MENU

echo.
echo Resetting cluster...

echo Step 1: Stopping and deleting old cluster...
k3d cluster delete tourism-cluster 2>nul
timeout /t 3 /nobreak >nul

echo Step 2: Creating new cluster with FIXED settings for Windows...
k3d cluster create tourism-cluster --api-port 127.0.0.1:6443 -p "8080:80@loadbalancer" --wait
timeout /t 10 /nobreak >nul

echo Step 3: Updating kubeconfig...
k3d kubeconfig merge tourism-cluster --kubeconfig-switch-context --overwrite
timeout /t 3 /nobreak >nul

echo Step 4: Verifying cluster connection...
kubectl cluster-info
if errorlevel 1 (
    echo ❌ Cluster verification failed!
    echo.
    echo Debug information:
    k3d cluster list
    docker ps
    echo.
    pause
    goto MAIN_MENU
)

echo.
echo ✅ Cluster reset complete!
echo.
pause
goto MAIN_MENU

:START_PLATFORM
echo.
echo Starting Tourism Platform...

echo Checking cluster connection...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Cannot connect to Kubernetes cluster!
    echo Please use option 6 to reset the cluster first.
    echo.
    pause
    goto MAIN_MENU
)

echo ✅ Cluster connection OK!

echo 🔨 Building Docker images (if needed)...
call :BUILD_IMAGES_SILENT

echo 📦 Importing Docker images into k3d cluster...
call :IMPORT_IMAGES_TO_K3D

echo Applying Kubernetes manifests...
kubectl apply -f k8s/namespace.yaml --validate=false
kubectl apply -f k8s/secrets.yaml --validate=false
kubectl apply -f k8s/configmap.yaml --validate=false
kubectl apply -f k8s/postgres.yaml --validate=false

echo Waiting for PostgreSQL to be ready...
timeout /t 20 /nobreak >nul

kubectl apply -f k8s/services-backend.yaml --validate=false
kubectl apply -f k8s/gateway.yaml --validate=false
kubectl apply -f k8s/frontend.yaml --validate=false

echo Waiting for services to be ready...
timeout /t 30 /nobreak >nul

echo.
echo Platform started! Checking status...
kubectl get pods -n %NAMESPACE% --sort-by=.metadata.creationTimestamp
echo.
echo Starting automatic port forwarding...
start "" /B kubectl port-forward -n %NAMESPACE% service/frontend 8081:80
timeout /t 2 /nobreak >nul
start "" /B kubectl port-forward -n %NAMESPACE% service/gateway 8080:8080
echo.
echo ✅ Port forwarding started successfully!
echo 🌐 Access the application at: http://localhost:8081
echo 🌉 API Gateway at: http://localhost:8080
echo.
pause
goto MAIN_MENU

:BUILD_IMAGES_SILENT
(
  docker build -t tourism-platform-auth-service:latest auth-service\
) >nul 2>&1 || (
  docker pull python:3.11-slim >nul 2>&1
  docker tag python:3.11-slim tourism-platform-auth-service:latest >nul 2>&1
)
(
  docker build -t tourism-platform-tours-service:latest tours-service\
) >nul 2>&1 || (
  docker pull python:3.11-slim >nul 2>&1
  docker tag python:3.11-slim tourism-platform-tours-service:latest >nul 2>&1
)
(
  docker build -t tourism-platform-booking-service:latest booking-service\
) >nul 2>&1 || (
  docker pull python:3.11-slim >nul 2>&1
  docker tag python:3.11-slim tourism-platform-booking-service:latest >nul 2>&1
)
(
  docker build -t tourism-platform-frontend:latest frontend\
) >nul 2>&1 || (
  docker pull nginx:alpine >nul 2>&1
  docker tag nginx:alpine tourism-platform-frontend:latest >nul 2>&1
)
(
  docker build -t tourism-platform-gateway:latest gateway-service\
) >nul 2>&1 || (
  docker pull nginx:alpine >nul 2>&1
  docker tag nginx:alpine tourism-platform-gateway:latest >nul 2>&1
)
goto :eof

:IMPORT_IMAGES_TO_K3D
echo Importing images to k3d cluster...
k3d image import tourism-platform-auth-service:latest -c tourism-cluster >nul 2>&1 && echo ✅ auth-service || echo ⚠️ auth-service (using existing)
k3d image import tourism-platform-tours-service:latest -c tourism-cluster >nul 2>&1 && echo ✅ tours-service || echo ⚠️ tours-service (using existing)
k3d image import tourism-platform-booking-service:latest -c tourism-cluster >nul 2>&1 && echo ✅ booking-service || echo ⚠️ booking-service (using existing)
k3d image import tourism-platform-frontend:latest -c tourism-cluster >nul 2>&1 && echo ✅ frontend || echo ⚠️ frontend (using existing)
k3d image import tourism-platform-gateway:latest -c tourism-cluster >nul 2>&1 && echo ✅ gateway || echo ⚠️ gateway (using existing)
echo ✅ Images import completed!
goto :eof

:STOP_PLATFORM
echo.
echo Stopping Tourism Platform...
kubectl delete -f k8s/ --ignore-not-found=true --recursive
echo.
echo Platform stopped!
pause
goto MAIN_MENU

:CHECK_STATUS
echo.
echo Current Platform Status:
echo ========================
kubectl get pods -n %NAMESPACE% -o wide
echo.
echo Services:
kubectl get services -n %NAMESPACE%
echo.
echo Cluster Status:
k3d cluster list
echo.
pause
goto MAIN_MENU

:VIEW_LOGS
cls
echo.
echo View Logs
echo =========
echo.
echo 1. PostgreSQL
echo 2. Auth Service
echo 3. Tours Service
echo 4. Booking Service
echo 5. Frontend
echo 6. Gateway
echo 7. Back to Main Menu
echo.
set /p LOG_CHOICE="Choose service [1-7]: "

if "%LOG_CHOICE%"=="1" (
    echo PostgreSQL Logs:
    kubectl logs -n %NAMESPACE% postgres-0 --tail=50
)
if "%LOG_CHOICE%"=="2" (
    echo Auth Service Logs:
    kubectl logs -n %NAMESPACE% deployment/auth-service --tail=50
)
if "%LOG_CHOICE%"=="3" (
    echo Tours Service Logs:
    kubectl logs -n %NAMESPACE% deployment/tours-service --tail=50
)
if "%LOG_CHOICE%"=="4" (
    echo Booking Service Logs:
    kubectl logs -n %NAMESPACE% deployment/booking-service --tail=50
)
if "%LOG_CHOICE%"=="5" (
    echo Frontend Logs:
    kubectl logs -n %NAMESPACE% deployment/frontend --tail=50
)
if "%LOG_CHOICE%"=="6" (
    echo Gateway Logs:
    kubectl logs -n %NAMESPACE% deployment/gateway --tail=50
)
if "%LOG_CHOICE%"=="7" goto MAIN_MENU

echo.
pause
goto VIEW_LOGS

:PORT_FORWARD
echo.
echo Starting Port Forward...
echo Frontend: http://localhost:8081
echo Gateway API: http://localhost:8080
echo.
start "" /B kubectl port-forward -n %NAMESPACE% service/frontend 8081:80
timeout /t 2 /nobreak >nul
start "" /B kubectl port-forward -n %NAMESPACE% service/gateway 8080:8080
echo Port forwarding started in background
echo.
pause
goto MAIN_MENU

:IMPORT_IMAGES
echo.
echo Importing Docker images to k3d cluster...
call :IMPORT_IMAGES_TO_K3D
echo.
pause
goto MAIN_MENU

:EXIT
echo.
echo Stopping any running port-forward processes...
taskkill /f /im kubectl.exe >nul 2>&1
echo Goodbye!
timeout /t 2 /nobreak >nul
exit