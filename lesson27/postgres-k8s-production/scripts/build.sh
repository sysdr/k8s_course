#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build Database API
cd apps/database-api
docker build -t database-api:latest .
kind load docker-image database-api:latest --name postgres-ha

# Build Frontend
cd ../frontend
docker build -t frontend:latest .
kind load docker-image frontend:latest --name postgres-ha

cd ../..
echo "All images built and loaded into kind cluster!"
