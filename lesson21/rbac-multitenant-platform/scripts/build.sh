#!/bin/bash
set -euo pipefail

echo "Building all Docker images..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Build services
echo "Building log-processor..."
docker build -t log-processor:latest ./services/log-processor

echo "Building analytics-api..."
docker build -t analytics-api:latest ./services/analytics-api

echo "Building audit-service..."
docker build -t audit-service:latest ./services/audit-service

echo "Building rbac-validator..."
docker build -t rbac-validator:latest ./services/rbac-validator

echo "Building frontend..."
docker build -t rbac-frontend:latest ./frontend

echo ""
echo "✓ All images built successfully!"
echo ""
echo "Images:"
docker images | grep -E "(log-processor|analytics-api|audit-service|rbac-validator|rbac-frontend)"
