#!/bin/bash
set -euo pipefail

echo "🏗️  Building container images..."

# Build log-processor
docker build -t log-processor:1.0.0 apps/log-processor/

# Build metrics-exporter
docker build -t metrics-exporter:1.0.0 apps/metrics-exporter/

# Build frontend
docker build -t observability-dashboard:1.0.0 apps/frontend/

echo "✅ All images built successfully!"

# If using kind, load images
if command -v kind &> /dev/null; then
    echo "Loading images into kind cluster..."
    kind load docker-image log-processor:1.0.0
    kind load docker-image metrics-exporter:1.0.0
    kind load docker-image observability-dashboard:1.0.0
fi
