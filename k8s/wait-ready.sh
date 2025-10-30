#!/usr/bin/env bash
set -euo pipefail
NAMESPACE=${1:-tourism}

echo "Waiting for deployments to be available..."
kubectl -n "$NAMESPACE" wait --for=condition=available --timeout=240s deploy/auth-service
kubectl -n "$NAMESPACE" wait --for=condition=available --timeout=240s deploy/tours-service
kubectl -n "$NAMESPACE" wait --for=condition=available --timeout=240s deploy/booking-service
kubectl -n "$NAMESPACE" wait --for=condition=available --timeout=240s deploy/frontend

echo "Waiting for postgres pod to be ready..."
kubectl -n "$NAMESPACE" wait --for=condition=ready pod -l app=postgres --timeout=240s
