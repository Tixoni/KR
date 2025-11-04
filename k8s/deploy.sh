#!/bin/bash
set -euo pipefail

NAMESPACE="tourism"
DOCKER_USER="${DOCKER_USERNAME:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

if [[ -z "$DOCKER_USER" ]]; then
  echo "DOCKER_USERNAME is required (pass as env or GitHub Secret)." >&2
  exit 1
fi

echo "Using namespace: $NAMESPACE"
echo "Using Docker Hub user: $DOCKER_USER"
echo "Using image tag: $IMAGE_TAG"

echo "Applying namespace and base resources..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml -n "$NAMESPACE"
kubectl apply -f k8s/secrets.yaml -n "$NAMESPACE"
kubectl apply -f k8s/postgres.yaml -n "$NAMESPACE"

echo "Waiting for database to be ready..."
sleep 30

echo "Applying services and deployments..."
kubectl apply -f k8s/services-backend.yaml -n "$NAMESPACE"
kubectl apply -f k8s/gateway.yaml -n "$NAMESPACE"
kubectl apply -f k8s/frontend.yaml -n "$NAMESPACE"

echo "Updating images from Docker Hub..."
kubectl set image deployment/auth-service auth-service="$DOCKER_USER/tourism-platform-auth-service:$IMAGE_TAG" -n "$NAMESPACE"
kubectl set image deployment/tours-service tours-service="$DOCKER_USER/tourism-platform-tours-service:$IMAGE_TAG" -n "$NAMESPACE"
kubectl set image deployment/booking-service booking-service="$DOCKER_USER/tourism-platform-booking-service:$IMAGE_TAG" -n "$NAMESPACE"
kubectl set image deployment/gateway gateway="$DOCKER_USER/tourism-platform-gateway:$IMAGE_TAG" -n "$NAMESPACE"
kubectl set image deployment/frontend frontend="$DOCKER_USER/tourism-platform-frontend:$IMAGE_TAG" -n "$NAMESPACE"

echo "Waiting for deployments to become available..."
kubectl rollout status deployment/auth-service -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/tours-service -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/booking-service -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/gateway -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=300s

echo "Deployment completed successfully! 🎉"