#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build ingestion API
docker build -t ingestion-api:latest services/ingestion-api/

# Build analytics engine
docker build -t analytics-engine:latest services/analytics-engine/
docker build -t analytics-engine-init:latest -f services/analytics-engine/Dockerfile.init services/analytics-engine/

# Build dashboard
docker build -t dashboard:latest services/dashboard/

echo "✓ All images built successfully"
