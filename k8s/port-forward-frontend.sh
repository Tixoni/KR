#!/usr/bin/env bash
set -euo pipefail
NAMESPACE=${1:-tourism}
LOCAL_PORT=${2:-8080}
TARGET_PORT=80

kubectl -n "$NAMESPACE" port-forward deploy/frontend "$LOCAL_PORT":"$TARGET_PORT" &
PF_PID=$!
echo $PF_PID > pf.pid
echo "Port-forward started on http://localhost:$LOCAL_PORT (PID=$PF_PID)"
