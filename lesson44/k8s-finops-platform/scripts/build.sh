#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"

echo "Building all Docker images..."

# Build backend services
cd backend/log-ingest
docker build -t log-ingest:latest .
cd ../..

cd backend/cost-analyzer
docker build -t cost-analyzer:latest .
cd ../..

# Build frontend
cd frontend/cost-dashboard
docker build -t cost-dashboard:latest .
cd ../..

# Load images into kind cluster
kind load docker-image log-ingest:latest --name finops-demo
kind load docker-image cost-analyzer:latest --name finops-demo
kind load docker-image cost-dashboard:latest --name finops-demo

echo "All images built and loaded!"
