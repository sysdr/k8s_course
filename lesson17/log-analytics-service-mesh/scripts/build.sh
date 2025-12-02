#!/bin/bash
set -euo pipefail

echo "=== Building Docker images ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Build images
echo "Building ingestion-api..."
docker build -t ingestion-api:latest "${PROJECT_ROOT}/services/ingestion-api"

echo "Building processing-service..."
docker build -t processing-service:latest "${PROJECT_ROOT}/services/processing-service"

echo "Building query-api..."
docker build -t query-api:latest "${PROJECT_ROOT}/services/query-api"

echo "Building dashboard..."
docker build -t dashboard:latest "${PROJECT_ROOT}/services/dashboard"

# Load images into kind cluster
echo "Loading images into kind cluster..."
kind load docker-image ingestion-api:latest --name log-analytics
kind load docker-image processing-service:latest --name log-analytics
kind load docker-image query-api:latest --name log-analytics
kind load docker-image dashboard:latest --name log-analytics

echo "✓ All images built and loaded successfully"
