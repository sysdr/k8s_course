#!/bin/bash
set -euo pipefail

echo "Building optimized container images..."

# Build Python API Service
echo "Building api-service..."
cd services/api-service
docker build -t api-service:latest .
echo "✓ api-service built: $(docker images api-service:latest --format '{{.Size}}')"
cd ../..

# Build Node.js Frontend
echo "Building frontend..."
cd services/frontend
docker build -t frontend:latest .
echo "✓ frontend built: $(docker images frontend:latest --format '{{.Size}}')"
cd ../..

# Build Go Log Processor
echo "Building log-processor..."
cd services/log-processor
docker build -t log-processor:latest .
echo "✓ log-processor built: $(docker images log-processor:latest --format '{{.Size}}')"
cd ../..

echo ""
echo "All images built successfully!"
echo "Image sizes:"
docker images | grep -E "(api-service|frontend|log-processor)" | grep latest
