#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build log ingestion service
cd services/log-ingestion
docker build -t log-ingestion:latest .
cd ../..

# Build log processor service
cd services/log-processor
docker build -t log-processor:latest .
cd ../..

# Build frontend
cd frontend
docker build -t frontend:latest .
cd ..

echo "All images built successfully!"
