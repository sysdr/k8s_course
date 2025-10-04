#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build log producer
cd services/log-producer
docker build -t log-producer:latest .
kind load docker-image log-producer:latest --name log-system

# Build log processor
cd ../log-processor
docker build -t log-processor:latest .
kind load docker-image log-processor:latest --name log-system

# Build frontend
cd ../frontend
docker build -t log-frontend:latest .
kind load docker-image log-frontend:latest --name log-system

echo "All images built and loaded into kind cluster!"
