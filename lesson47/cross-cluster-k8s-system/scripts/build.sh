#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Building Docker images (project root: $PROJECT_ROOT)..."

# Build Cluster A images
echo "Building log-ingestion service..."
docker build -t log-ingestion:latest cluster-a/services/log-ingestion/

# Build Cluster B images
echo "Building log-processor service..."
docker build -t log-processor:latest cluster-b/services/log-processor/

# Load images into kind clusters (if kind is available)
if command -v kind &>/dev/null; then
  echo "Loading images into kind clusters..."
  kind load docker-image log-ingestion:latest --name cluster-a
  kind load docker-image log-processor:latest --name cluster-b
else
  echo "kind not found - skipping image load (use docker-compose for local run)"
fi

echo "Build complete!"
