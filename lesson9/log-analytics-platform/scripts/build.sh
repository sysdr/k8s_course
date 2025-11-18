#!/bin/bash
set -euo pipefail

echo "Building all Docker images for log analytics platform..."

# Load images into kind cluster
CLUSTER_NAME="log-analytics"

# Build API Gateway
echo "Building api-gateway..."
docker build -t api-gateway:latest services/api-gateway/
kind load docker-image api-gateway:latest --name ${CLUSTER_NAME}

# Build Log Ingestion
echo "Building log-ingestion..."
docker build -t log-ingestion:latest services/log-ingestion/
kind load docker-image log-ingestion:latest --name ${CLUSTER_NAME}

# Build Log Processor
echo "Building log-processor..."
docker build -t log-processor:latest services/log-processor/
kind load docker-image log-processor:latest --name ${CLUSTER_NAME}

# Build Query Service
echo "Building query-service..."
docker build -t query-service:latest services/query-service/
kind load docker-image query-service:latest --name ${CLUSTER_NAME}

# Build Frontend
echo "Building frontend..."
docker build -t frontend:latest frontend/
kind load docker-image frontend:latest --name ${CLUSTER_NAME}

echo "All images built and loaded into kind cluster successfully!"
