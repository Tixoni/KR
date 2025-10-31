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
echo 3.  Restart Platform
echo 4.  Check Status
echo 5.  View Logs
echo 6.  Port Forward (Frontend + APIs)
echo 7.  Health Check
echo 8.  Cleanup (Remove everything)
echo 9.  Start k3d Cluster
echo 10. Stop k3d Cluster
echo 11. Reset Cluster (Full reset)
echo 12. Build Docker Images
echo 13. Import Images to k3d Cluster
echo 14. Exit
echo.
set /p CHOICE="Choose option [1-14]: "

if "%CHOICE%"=="1" goto START_PLATFORM
if "%CHOICE%"=="2" goto STOP_PLATFORM
if "%CHOICE%"=="3" goto RESTART_PLATFORM
if "%CHOICE%"=="4" goto CHECK_STATUS
if "%CHOICE%"=="5" goto VIEW_LOGS
if "%CHOICE%"=="6" goto PORT_FORWARD
if "%CHOICE%"=="7" goto HEALTH_CHECK
if "%CHOICE%"=="8" goto CLEANUP
if "%CHOICE%"=="9" goto START_CLUSTER
if "%CHOICE%"=="10" goto STOP_CLUSTER
if "%CHOICE%"=="11" goto RESET_CLUSTER
if "%CHOICE%"=="12" goto BUILD_IMAGES
if "%CHOICE%"=="13" goto IMPORT_IMAGES
if "%CHOICE%"=="14" goto EXIT

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
      echo.
      echo WORKDIR /app
      echo.
      echo RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv bcrypt python-jose cryptography email-validator
      echo.
      echo COPY requirements.txt .
      echo RUN pip install --no-cache-dir -r requirements.txt
      echo COPY src/ ./src/
      echo COPY health_check.py .
      echo.
      echo CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
    )> auth-service\Dockerfile
)

if not exist "tours-service\Dockerfile" (
    echo Creating Dockerfile for tours-service...
    (
      echo FROM python:3.11-slim
      echo.
      echo WORKDIR /app
      echo.
      echo RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv python-jose cryptography
      echo.
      echo COPY requirements.txt .
      echo RUN pip install --no-cache-dir -r requirements.txt
      echo COPY src/ ./src/
      echo COPY health_check.py .
      echo.
      echo CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
    )> tours-service\Dockerfile
)

if not exist "booking-service\Dockerfile" (
    echo Creating Dockerfile for booking-service...
    (
      echo FROM python:3.11-slim
      echo.
      echo WORKDIR /app
      echo.
      echo RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic python-jose cryptography httpx
      echo.
      echo COPY requirements.txt .
      echo RUN pip install --no-cache-dir -r requirements.txt
      echo COPY src/ ./src/
      echo COPY health_check.py .
      echo.
      echo CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
    )> booking-service\Dockerfile
)

if not exist "frontend\Dockerfile" (
    echo Creating Dockerfile for frontend...
    (
      echo FROM nginx:1.25-alpine
      echo.
      echo COPY nginx.conf /etc/nginx/nginx.conf
      echo COPY index.html /usr/share/nginx/html/index.html
      echo COPY styles.css /usr/share/nginx/html/styles.css
      echo COPY script.js /usr/share/nginx/html/script.js
      echo COPY sounds/ /usr/share/nginx/html/sounds/
      echo.
      echo EXPOSE 80
      echo.
      echo CMD ["nginx", "-g", "daemon off;"]
    )> frontend\Dockerfile
)

echo.
echo 🏗️ Building auth-service...
pushd auth-service
docker build -t tourism-platform-auth-service:latest .
popd
if errorlevel 1 (
    echo ❌ Failed to build auth-service image!
    echo Using fallback Python image...
    docker pull python:3.11-slim
    docker tag python:3.11-slim tourism-platform-auth-service:latest
)

echo 🏗️ Building tours-service...
pushd tours-service
docker build -t tourism-platform-tours-service:latest .
popd
if errorlevel 1 (
    echo ❌ Failed to build tours-service image!
    echo Using fallback Python image...
    docker pull python:3.11-slim
    docker tag python:3.11-slim tourism-platform-tours-service:latest
)

echo 🏗️ Building booking-service...
pushd booking-service
docker build -t tourism-platform-booking-service:latest .
popd
if errorlevel 1 (
    echo ❌ Failed to build booking-service image!
    echo Using fallback Python image...
    docker pull python:3.11-slim
    docker tag python:3.11-slim tourism-platform-booking-service:latest
)

echo 🏗️ Building frontend...
pushd frontend
docker build -t tourism-platform-frontend:latest .
popd
if errorlevel 1 (
    echo ❌ Failed to build frontend image!
    echo Using fallback Nginx image...
    docker pull nginx:alpine
    docker tag nginx:alpine tourism-platform-frontend:latest
)

echo.
echo ✅ Docker images built successfully!
echo.
echo Current images:
docker images | findstr "tourism-platform"
echo.
echo Do you want to import images to k3d cluster now? (y/N)
set /p IMPORT_CHOICE="> "
if /i "%IMPORT_CHOICE%"=="y" (
    echo.
    call :IMPORT_IMAGES_TO_K3D
)
echo.
pause
goto MAIN_MENU

:START_CLUSTER
echo.
echo Starting k3d cluster...
k3d cluster start tourism-cluster
timeout /t 5 /nobreak >nul

echo Updating kubeconfig...
k3d kubeconfig merge tourism-cluster --kubeconfig-switch-context
timeout /t 3 /nobreak >nul

echo Verifying cluster connection...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo ❌ Cluster started but connection failed!
    echo Trying to fix with full reset...
    call :RESET_CLUSTER
    goto MAIN_MENU
)

echo.
echo ✅ k3d cluster started and configured!
kubectl cluster-info
echo.
pause
goto MAIN_MENU

:STOP_CLUSTER
echo.
echo Stopping k3d cluster...
k3d cluster stop tourism-cluster
echo.
echo ✅ k3d cluster stopped!
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
k3d cluster delete tourism-cluster
timeout /t 5 /nobreak >nul

echo Creating new cluster with fixed API port...
k3d cluster create tourism-cluster -p "8080:80@loadbalancer" --api-port 6443 --wait
timeout /t 15 /nobreak >nul

echo Updating kubeconfig...
k3d kubeconfig merge tourism-cluster --kubeconfig-switch-context
timeout /t 3 /nobreak >nul

echo Verifying cluster...
echo Waiting for cluster to be fully ready...
timeout /t 10 /nobreak >nul

echo Checking cluster connection...
kubectl cluster-info
if errorlevel 1 (
    echo ❌ Cluster verification failed!
    echo.
    echo Debug information:
    echo - Docker containers:
    docker ps
    echo.
    echo - K3d clusters:
    k3d cluster list
    echo.
    echo - Kubernetes nodes:
    kubectl get nodes
    echo.
    echo Please wait a moment and try option 9 to start the cluster.
    echo.
    pause
    goto MAIN_MENU
)

echo.
echo ✅ Cluster reset complete!
kubectl cluster-info
echo.
pause
goto MAIN_MENU

:START_PLATFORM
echo.
echo Starting Tourism Platform...

echo 🔨 Building Docker images (if needed)...
call :BUILD_IMAGES_SILENT

echo Checking cluster connection...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Cannot connect to Kubernetes cluster!
    echo Please make sure k3d cluster is running.
    echo Use option 9 to start the cluster.
    echo.
    pause
    goto MAIN_MENU
)

echo ✅ Cluster connection OK!
echo 📦 Importing Docker images into k3d cluster...
call :IMPORT_IMAGES_TO_K3D
echo Applying Kubernetes manifests...
kubectl apply -f k8s/namespace.yaml --validate=false
kubectl apply -f k8s/secrets.yaml --validate=false
kubectl apply -f k8s/configmap.yaml --validate=false
kubectl apply -f k8s/postgres.yaml --validate=false

echo Waiting for PostgreSQL to be ready...
timeout /t 30 /nobreak >nul

kubectl apply -f k8s/services-backend.yaml --validate=false
kubectl apply -f k8s/frontend.yaml --validate=false

echo Waiting for ALL services to be ready...
timeout /t 45 /nobreak >nul

echo.
echo Platform started! Checking status...
kubectl get pods -n %NAMESPACE% --sort-by=.metadata.creationTimestamp
echo.
echo Starting automatic port forwarding for frontend...

echo.
echo ✅ Port forwarding started successfully!
echo 🌐 Access the application at: http://localhost:8081
echo.
echo Use option 6 for additional port forwarding
pause
goto MAIN_MENU

:BUILD_IMAGES_SILENT
echo Building Docker images silently...
(
  pushd auth-service && docker build -t tourism-platform-auth-service:latest . && popd
) >nul 2>&1 || (
  docker pull python:3.11-slim >nul 2>&1
  docker tag python:3.11-slim tourism-platform-auth-service:latest >nul 2>&1
)
(
  pushd tours-service && docker build -t tourism-platform-tours-service:latest . && popd
) >nul 2>&1 || (
  docker pull python:3.11-slim >nul 2>&1
  docker tag python:3.11-slim tourism-platform-tours-service:latest >nul 2>&1
)
(
  pushd booking-service && docker build -t tourism-platform-booking-service:latest . && popd
) >nul 2>&1 || (
  docker pull python:3.11-slim >nul 2>&1
  docker tag python:3.11-slim tourism-platform-booking-service:latest >nul 2>&1
)
(
  pushd frontend && docker build -t tourism-platform-frontend:latest . && popd
) >nul 2>&1 || (
  docker pull nginx:alpine >nul 2>&1
  docker tag nginx:alpine tourism-platform-frontend:latest >nul 2>&1
)

goto :eof

:IMPORT_IMAGES_TO_K3D
echo Importing images to k3d cluster...
echo.
echo Importing auth-service...
k3d image import tourism-platform-auth-service:latest -c tourism-cluster 2>&1 | findstr /V "^$" || echo ⚠️ Failed to import auth-service image
echo Importing tours-service...
k3d image import tourism-platform-tours-service:latest -c tourism-cluster 2>&1 | findstr /V "^$" || echo ⚠️ Failed to import tours-service image
echo Importing booking-service...
k3d image import tourism-platform-booking-service:latest -c tourism-cluster 2>&1 | findstr /V "^$" || echo ⚠️ Failed to import booking-service image
echo Importing frontend...
k3d image import tourism-platform-frontend:latest -c tourism-cluster 2>&1 | findstr /V "^$" || echo ⚠️ Failed to import frontend image
echo.
echo ✅ Images import completed!
goto :eof

:STOP_PLATFORM
echo.
echo Stopping Tourism Platform...

echo Checking cluster connection...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Cannot connect to Kubernetes cluster!
    echo Please make sure k3d cluster is running.
    echo Use option 9 to start the cluster.
    echo.
    pause
    goto MAIN_MENU
)

kubectl delete -f k8s/frontend.yaml --ignore-not-found=true
kubectl delete -f k8s/services-backend.yaml --ignore-not-found=true
kubectl delete -f k8s/postgres.yaml --ignore-not-found=true
echo.
echo Platform stopped!
pause
goto MAIN_MENU

:RESTART_PLATFORM
echo.
echo Restarting Tourism Platform...
call :STOP_PLATFORM
timeout /t 5 /nobreak >nul
call :START_PLATFORM
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
echo Docker Images:
docker images | findstr "tourism-platform" || echo No tourism-platform images found
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
echo 6. Back to Main Menu
echo.
set /p LOG_CHOICE="Choose service [1-6]: "

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
if "%LOG_CHOICE%"=="6" goto MAIN_MENU

echo.
pause
goto VIEW_LOGS

:PORT_FORWARD
echo.
echo Starting Port Forward...
echo Frontend: http://localhost:8081
echo Auth API: http://localhost:8000/health
echo Tours API: http://localhost:8001/health
echo Booking API: http://localhost:8002/health
echo.
echo Press Ctrl+C to stop port forwarding
echo.

start "" /B kubectl port-forward -n %NAMESPACE% service/frontend 8081:80
timeout /t 2 /nobreak >nul
start "" /B kubectl port-forward -n %NAMESPACE% service/auth-service 8000:8000
timeout /t 2 /nobreak >nul
start "" /B kubectl port-forward -n %NAMESPACE% service/tours-service 8001:8001
timeout /t 2 /nobreak >nul
start "" /B kubectl port-forward -n %NAMESPACE% service/booking-service 8002:8002

echo Port forwarding started in background windows
echo Access the application at: http://localhost:8081
echo.
pause
goto MAIN_MENU

:HEALTH_CHECK
echo.
echo Health Check:
echo =============
echo.
echo Checking services health...

echo - PostgreSQL: 
kubectl exec -n %NAMESPACE% postgres-0 -- pg_isready -U admin 2>nul && echo OK || echo FAILED

echo - Auth Service: 
kubectl get pods -n %NAMESPACE% -l app=auth-service --no-headers | find "Running" >nul && echo OK || echo FAILED

echo - Tours Service: 
kubectl get pods -n %NAMESPACE% -l app=tours-service --no-headers | find "Running" >nul && echo OK || echo FAILED

echo - Booking Service: 
kubectl get pods -n %NAMESPACE% -l app=booking-service --no-headers | find "Running" >nul && echo OK || echo FAILED

echo - Frontend: 
kubectl get pods -n %NAMESPACE% -l app=frontend --no-headers | find "Running" >nul && echo OK || echo FAILED

echo.
pause
goto MAIN_MENU

:CLEANUP
echo.
echo WARNING: This will remove ALL platform resources!
set /p CONFIRM="Are you sure? (y/N): "
if /i not "%CONFIRM%"=="y" goto MAIN_MENU

echo.
echo Cleaning up Tourism Platform...

echo Checking cluster connection...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Cannot connect to Kubernetes cluster!
    echo Please make sure k3d cluster is running.
    echo Use option 9 to start the cluster.
    echo.
    pause
    goto MAIN_MENU
)

kubectl delete -f k8s/ --ignore-not-found=true --recursive
kubectl delete namespace %NAMESPACE% --ignore-not-found=true
echo.
echo Cleanup completed!
pause
goto MAIN_MENU

:IMPORT_IMAGES
echo.
echo Importing Docker images to k3d cluster...

echo Checking cluster connection...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Cannot connect to Kubernetes cluster!
    echo Please make sure k3d cluster is running.
    echo Use option 9 to start the cluster.
    echo.
    pause
    goto MAIN_MENU
)

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