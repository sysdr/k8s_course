#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build all services
docker build -t log-collector:latest ./src/log-collector
docker build -t log-processor:latest ./src/log-processor
docker build -t analytics-api:latest ./src/analytics-api
docker build -t frontend:latest ./src/frontend

echo "All images built successfully"
docker images | grep -E "log-collector|log-processor|analytics-api|frontend"
