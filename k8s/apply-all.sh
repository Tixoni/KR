#!/usr/bin/env bash
set -euo pipefail
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/services-backend.yaml
kubectl apply -f k8s/frontend.yaml
