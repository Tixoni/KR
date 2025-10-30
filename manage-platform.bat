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
echo 11. Exit
echo.
set /p CHOICE="Choose option [1-11]: "

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
if "%CHOICE%"=="11" goto EXIT

echo Invalid choice! Press any key to continue...
pause >nul
goto MAIN_MENU

:START_CLUSTER
echo.
echo Starting k3d cluster...
k3d cluster start tourism-cluster
echo.
echo ✅ k3d cluster started!
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

:START_PLATFORM
echo.
echo Starting Tourism Platform...
echo Applying Kubernetes manifests...
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres.yaml

echo Waiting for PostgreSQL to be ready...
timeout /t 20 /nobreak >nul

kubectl apply -f k8s/services-backend.yaml
kubectl apply -f k8s/frontend.yaml

echo Waiting for ALL services to be ready...
timeout /t 30 /nobreak >nul

echo.
echo Platform started! Checking status...
kubectl get pods -n %NAMESPACE% --sort-by=.metadata.creationTimestamp
echo.
echo Starting automatic port forwarding for frontend...

start "Frontend Port Forward" kubectl port-forward -n %NAMESPACE% service/frontend 8081:80
timeout /t 3 /nobreak >nul

echo.
echo ✅ Port forwarding started successfully!
echo 🌐 Access the application at: http://localhost:8081
echo.
echo Use option 6 for additional port forwarding
pause
goto MAIN_MENU

:STOP_PLATFORM
echo.
echo Stopping Tourism Platform...
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
kubectl delete -f k8s/ --ignore-not-found=true --recursive
kubectl delete namespace %NAMESPACE% --ignore-not-found=true
echo.
echo Cleanup completed!
pause
goto MAIN_MENU

:EXIT
echo.
echo Stopping any running port-forward processes...
taskkill /f /im kubectl.exe >nul 2>&1
echo Goodbye!
timeout /t 2 /nobreak >nul
exit