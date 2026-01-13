#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_ROOT"

# Validate paths before executing
if [ ! -d "services/producer" ]; then
    echo "Error: services/producer directory not found. Current directory: $(pwd)"
    exit 1
fi

echo "Building Docker images..."

# Build producer
echo "Building producer image..."
docker build -t producer:latest services/producer/

# Build consumer
echo "Building consumer image..."
docker build -t consumer:latest services/consumer/

# Build API
echo "Building API image..."
docker build -t api:latest services/api/

# Build frontend
echo "Building frontend image..."
cd frontend
docker build -t frontend:latest .
cd ..

echo "All images built successfully!"
