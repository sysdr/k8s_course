#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build log-ingestion
docker build -t log-ingestion:latest ./services/log-ingestion

# Build analytics-engine
docker build -t analytics-engine:latest ./services/analytics-engine

# Build dashboard
docker build -t dashboard:latest ./services/dashboard

# Load images into kind
kind load docker-image log-ingestion:latest --name log-analytics
kind load docker-image analytics-engine:latest --name log-analytics
kind load docker-image dashboard:latest --name log-analytics

echo "Images built and loaded successfully!"
