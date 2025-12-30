#!/bin/bash
set -euo pipefail

echo "🔨 Building Docker images..."

# Build backend
echo "Building backend image..."
docker build -t transaction-api:latest ./backend

# Build frontend
echo "Building frontend image..."
docker build -t transaction-frontend:latest ./frontend

# Load images into kind cluster
echo "Loading images into kind cluster..."
kind load docker-image transaction-api:latest --name transaction-system || echo "⚠️ Failed to load backend image"
kind load docker-image transaction-frontend:latest --name transaction-system || echo "⚠️ Failed to load frontend image"

echo "✅ Build complete!"
