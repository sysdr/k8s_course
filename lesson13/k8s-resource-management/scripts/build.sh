#!/bin/bash
set -euo pipefail

echo "Building Docker images..."

# Build services
docker build -t log-ingest:latest ./services/log-ingest
docker build -t log-parser:latest ./services/log-parser
docker build -t analytics-engine:latest ./services/analytics-engine
docker build -t frontend:latest ./frontend

echo "✓ All images built successfully"
docker images | grep -E "(log-ingest|log-parser|analytics-engine|frontend)"
