#!/bin/bash

# Скрипт для сборки Docker образов для Kubernetes

echo "Сборка Docker образов для Kubernetes..."

echo "Сборка auth-service..."
docker build -t auth-service:latest ./backend/authentification_service/

echo "Сборка data-service..."
docker build -t data-service:latest ./backend/data_service/

echo "Сборка processing-service..."
docker build -t processing-service:latest ./backend/processing_service/

echo "Сборка frontend..."
docker build -t frontend:latest ./frontend/

echo "Все образы собраны успешно!"

