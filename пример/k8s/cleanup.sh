#!/bin/bash

# Скрипт для очистки Kubernetes ресурсов

echo "Очистка Kubernetes ресурсов..."

# Удаление всех ресурсов в правильном порядке
echo "Удаление Ingress..."
kubectl delete -f k8s/ingress.yaml --ignore-not-found=true

echo "Удаление Frontend..."
kubectl delete -f k8s/frontend-deployment.yaml --ignore-not-found=true

echo "Удаление Processing Service..."
kubectl delete -f k8s/processing-deployment.yaml --ignore-not-found=true

echo "Удаление Data Service..."
kubectl delete -f k8s/data-deployment.yaml --ignore-not-found=true

echo "Удаление Auth Service..."
kubectl delete -f k8s/auth-deployment.yaml --ignore-not-found=true

echo "Удаление PostgreSQL..."
kubectl delete -f k8s/postgres-deployment.yaml --ignore-not-found=true

echo "Удаление PersistentVolumeClaims..."
kubectl delete -f k8s/persistent-volume-claim.yaml --ignore-not-found=true

echo "Удаление PersistentVolumes..."
kubectl delete -f k8s/persistent-volume.yaml --ignore-not-found=true

echo "Удаление Secrets..."
kubectl delete -f k8s/secret.yaml --ignore-not-found=true

echo "Удаление ConfigMaps..."
kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
kubectl delete -f k8s/nginx-configmap.yaml --ignore-not-found=true

echo "Удаление Namespace..."
kubectl delete -f k8s/namespace.yaml --ignore-not-found=true

echo "Очистка завершена!"