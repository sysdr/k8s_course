#!/bin/bash
set -euo pipefail

echo "Building container images..."

# Load images into kind cluster
KIND_CLUSTER="gitops-drift"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
KIND_CMD="kind"
if [ -f "$BASE_DIR/kind" ]; then
    KIND_CMD="$BASE_DIR/kind"
fi

# Build API service
echo "Building API service..."
cd "$BASE_DIR/apps/api-service"
docker build -t api-service:latest .
$KIND_CMD load docker-image api-service:latest --name $KIND_CLUSTER
cd "$BASE_DIR"

# Build Frontend
echo "Building Frontend..."
cd "$BASE_DIR/apps/frontend"
docker build -t frontend:latest .
$KIND_CMD load docker-image frontend:latest --name $KIND_CLUSTER
cd "$BASE_DIR"

# Build Worker
echo "Building Worker..."
cd "$BASE_DIR/apps/worker"
docker build -t worker:latest .
$KIND_CMD load docker-image worker:latest --name $KIND_CLUSTER
cd "$BASE_DIR"

echo "All images built and loaded into kind cluster!"
