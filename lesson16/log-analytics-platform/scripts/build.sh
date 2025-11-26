#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

cd "$(dirname "$0")/.."

# Build backend services
echo "Building log-ingestion service..."
docker build -t log-ingestion:1.0.0 ./services/log-ingestion

echo "Building query service..."
docker build -t query-service:1.0.0 ./services/query-service

echo "Building analytics service..."
docker build -t analytics-service:1.0.0 ./services/analytics-service

echo "Building frontend..."
docker build -t frontend:1.0.0 ./frontend

echo "✓ All images built successfully!"

# List images
echo ""
echo "Built images:"
docker images | grep -E "log-ingestion|query-service|analytics-service|frontend"
