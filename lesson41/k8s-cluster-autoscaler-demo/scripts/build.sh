#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build services
docker build -t log-ingestion:latest ./services/log-ingestion
docker build -t log-processor:latest ./services/log-processor
docker build -t analytics-api:latest ./services/analytics-api
docker build -t frontend:latest ./frontend

echo "Docker images built successfully"
echo ""
echo "Loading images into kind cluster..."
kind load docker-image log-ingestion:latest --name log-platform-cluster
kind load docker-image log-processor:latest --name log-platform-cluster
kind load docker-image analytics-api:latest --name log-platform-cluster
kind load docker-image frontend:latest --name log-platform-cluster

echo "Images loaded successfully"
