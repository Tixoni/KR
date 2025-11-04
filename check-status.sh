#!/bin/bash

# check-status.sh - Kubernetes status checker for Tourism Platform on k3d
set -euo pipefail

# Configuration
NAMESPACE="tourism"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🔍 Checking Tourism Platform (k8s/k3d) at $TIMESTAMP..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }

check_http() {
  local name=$1 url=$2
  if curl -fsS "$url" >/dev/null 2>&1; then
    print_status "$name: Healthy"
  else
    print_error "$name: Unhealthy"
  fi
}

show_logs() {
  local kind=$1 name=$2 lines=${3:-100}
  print_info "Recent logs for $kind/$name (last $lines lines):"
  kubectl logs -n "$NAMESPACE" "$kind/$name" --tail="$lines" 2>/dev/null || print_warning "No logs available"
}

show_resource_usage() {
  print_info "Cluster nodes:"; kubectl get nodes -o wide || true
  echo ""; print_info "Namespace resources in $NAMESPACE:"; kubectl get all -n "$NAMESPACE" || true
}

rollout_status() {
  local deploy=$1
  kubectl rollout status -n "$NAMESPACE" deployment/"$deploy" --timeout=10s >/dev/null 2>&1 \
    && print_status "deployment/$deploy ready" \
    || print_warning "deployment/$deploy not ready yet"
}

main() {
  if ! command -v kubectl >/dev/null 2>&1; then
    print_error "kubectl not found"; exit 1; fi
  if command -v k3d >/dev/null 2>&1; then
    print_info "k3d clusters:"; k3d cluster list || true
  else
    print_warning "k3d not found (skipping cluster listing)"
  fi

  print_info "Kubernetes context:"; kubectl config current-context || true

  if ! kubectl get ns "$NAMESPACE" >/dev/null 2>&1; then
    print_error "namespace '$NAMESPACE' not found"; exit 1; fi

  echo ""; print_info "Pods:"; kubectl get pods -n "$NAMESPACE" -o wide
  echo ""; print_info "Services:"; kubectl get svc -n "$NAMESPACE"
  echo ""; print_info "Deployments:"; kubectl get deploy -n "$NAMESPACE"

  echo ""; print_info "Rollout status:";
  rollout_status auth-service
  rollout_status tours-service
  rollout_status booking-service
  rollout_status frontend
  rollout_status gateway || true

  echo ""; print_info "Health checks via port-forwards (if active):"
  check_http "frontend" "http://localhost:8081/" || true
  check_http "gateway" "http://localhost:8080/api/auth/health" || true

  echo ""; show_resource_usage

  echo ""; print_info "Useful commands:"
  echo "  kubectl get pods -n $NAMESPACE"
  echo "  kubectl logs -n $NAMESPACE deployment/auth-service"
  echo "  kubectl describe pod -n $NAMESPACE <pod>"
}

case "${1:-}" in
  --logs)
    kind="${2:-deployment}"; name="${3:-auth-service}"; lines="${4:-100}"; show_logs "$kind" "$name" "$lines" ;;
  --resources)
    show_resource_usage ;;
  -h|--help)
    echo "Usage: $0 [--logs [deployment|pod] NAME [LINES]] [--resources]" ;;
  *)
    main "$@" ;;
esac