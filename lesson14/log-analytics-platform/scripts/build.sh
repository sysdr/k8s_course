#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Building Docker images..."
echo "Project root: ${PROJECT_ROOT}"

# Build log-ingester
cd "${PROJECT_ROOT}/services/log-ingester"
docker build -t log-ingester:1.0.0 .
echo "✓ Built log-ingester:1.0.0"

# Build query-api
cd "${PROJECT_ROOT}/services/query-api"
docker build -t query-api:1.0.0 .
echo "✓ Built query-api:1.0.0"

# Build aggregator
cd "${PROJECT_ROOT}/services/aggregator"
docker build -t aggregator:1.0.0 .
echo "✓ Built aggregator:1.0.0"

# Build frontend
cd "${PROJECT_ROOT}/frontend"
docker build -t frontend:1.0.0 .
echo "✓ Built frontend:1.0.0"

echo "All images built successfully!"
