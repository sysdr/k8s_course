#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Building Docker images..."

# Build log-collector
docker build -t log-collector:latest "${PROJECT_ROOT}/src/log-collector"

# Build log-processor
docker build -t log-processor:latest "${PROJECT_ROOT}/src/log-processor"

# Build log-api
docker build -t log-api:latest "${PROJECT_ROOT}/src/log-api"

# Build frontend
docker build -t log-frontend:latest "${PROJECT_ROOT}/src/frontend"

echo "All images built successfully!"
docker images | grep -E "log-collector|log-processor|log-api|log-frontend"
