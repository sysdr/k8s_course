#!/bin/bash

set -euo pipefail

echo "🔨 Building container images..."

cd "$(dirname "$0")/.."

# Build frontend
echo "Building frontend..."
docker build -t ecommerce-frontend:latest ./frontend

# Build backend
echo "Building backend..."
docker build -t ecommerce-backend:latest ./backend

# Build dashboard
echo "Building dashboard..."
docker build -t dashboard:latest ./dashboard

echo "✅ Build complete!"
docker images | grep -E "(ecommerce|dashboard)"
