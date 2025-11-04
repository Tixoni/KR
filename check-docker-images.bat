@echo off
setlocal enabledelayedexpansion

if "%1"=="" (
  echo Usage: %~nx0 DOCKER_USERNAME [IMAGE_TAG]
  echo Example: %~nx0 tixongomzuak latest
  exit /b 1
)

set DOCKER_USERNAME=%~1
set IMAGE_TAG=%~2
if "%IMAGE_TAG%"=="" set IMAGE_TAG=latest

echo Checking local Docker images for %DOCKER_USERNAME% with tag %IMAGE_TAG% ...

docker images | findstr /i "%DOCKER_USERNAME%" | findstr /i "%IMAGE_TAG%"

if %errorlevel% neq 0 (
  echo No matching local images found. This does not check Docker Hub.
  echo To verify on Docker Hub, run (Linux/Mac/WSL):
  echo   docker manifest inspect %DOCKER_USERNAME%/tourism-platform-auth-service:%IMAGE_TAG%
  exit /b 1
) else (
  echo.
  echo If you see your images above, they are present locally.
  echo Remember to set GitHub Secret: DOCKER_USERNAME = %DOCKER_USERNAME%
)

endlocal
