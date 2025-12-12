#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build log ingestion service
docker build -t log-ingestion:latest ./services/log-ingestion

# Build log processor service
docker build -t log-processor:latest ./services/log-processor

# Build log query service
docker build -t log-query:latest ./services/log-query

# Build security dashboard
docker build -t security-dashboard:latest ./frontend/security-dashboard

echo "All images built successfully!"
docker images | grep -E "log-ingestion|log-processor|log-query|security-dashboard"
