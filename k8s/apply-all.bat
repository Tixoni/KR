@echo off
setlocal enabledelayedexpansion
kubectl apply -f k8s\namespace.yaml || goto :error
kubectl apply -f k8s\secrets.yaml || goto :error
kubectl apply -f k8s\configmap.yaml || goto :error
kubectl apply -f k8s\postgres.yaml || goto :error
kubectl apply -f k8s\services-backend.yaml || goto :error
kubectl apply -f k8s\frontend.yaml || goto :error

echo Done.
exit /b 0

:error
echo Failed.
exit /b 1
