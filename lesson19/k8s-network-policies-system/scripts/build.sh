#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build backend services
docker build -t api-gateway:latest ./services/api-gateway
docker build -t log-ingestion:latest ./services/log-ingestion
docker build -t log-processor:latest ./services/log-processor
docker build -t analytics-service:latest ./services/analytics-service

# Build frontend
docker build -t log-analytics-dashboard:latest ./frontend

echo "✓ All images built successfully"
