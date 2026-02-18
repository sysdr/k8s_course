#!/bin/bash
set -euo pipefail

echo "🔨 Building all container images..."

cd "$(dirname "$0")/.."

# Build log-ingestion service
echo "📦 Building log-ingestion..."
docker build -t log-ingestion:latest ./services/log-ingestion

# Build log-processor service
echo "📦 Building log-processor..."
docker build -t log-processor:latest ./services/log-processor

# Build analytics-api service
echo "📦 Building analytics-api..."
docker build -t analytics-api:latest ./services/analytics-api

# Build frontend
echo "📦 Building frontend..."
docker build -t frontend:latest ./frontend

echo "✅ All images built successfully!"
docker images | grep -E "log-ingestion|log-processor|analytics-api|frontend"
