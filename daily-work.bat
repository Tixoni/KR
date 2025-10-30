@echo off
chcp 65001 >nul
echo Daily Workflow Manager
echo =====================
echo.
echo 1. Start k3d cluster and Platform
echo 2. Stop Platform and k3d cluster  
echo 3. Exit
echo.
set /p DAILY_CHOICE="Choose option [1-3]: "

if "%DAILY_CHOICE%"=="1" (
    echo Starting k3d cluster...
    k3d cluster start tourism-cluster
    timeout /t 10 /nobreak >nul
    echo Starting Tourism Platform...
    call start-platform.bat
)
if "%DAILY_CHOICE%"=="2" (
    echo Stopping Tourism Platform...
    kubectl delete -f k8s/ --ignore-not-found=true --recursive
    timeout /t 5 /nobreak >nul
    echo Stopping k3d cluster...
    k3d cluster stop tourism-cluster
    echo.
    echo Everything stopped!
    pause
)
if "%DAILY_CHOICE%"=="3" exit