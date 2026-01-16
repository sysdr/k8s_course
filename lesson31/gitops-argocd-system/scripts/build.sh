#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Building Docker images..."

# Build metrics aggregator
echo "Building metrics-aggregator..."
docker build -t metrics-aggregator:latest "${PROJECT_ROOT}/apps/metrics-aggregator/"

# Build event processor
echo "Building event-processor..."
docker build -t event-processor:latest "${PROJECT_ROOT}/apps/event-processor/"

# Build dashboard
echo "Building dashboard..."
docker build -t dashboard:latest "${PROJECT_ROOT}/apps/dashboard/"

# Load images into kind
echo "Loading images into kind cluster..."
# Use local kind binary if available
if command -v kind &> /dev/null; then
    KIND_CMD="kind"
elif [ -f "${SCRIPT_DIR}/kind" ]; then
    KIND_CMD="${SCRIPT_DIR}/kind"
else
    echo "Error: kind not found"
    exit 1
fi

${KIND_CMD} load docker-image metrics-aggregator:latest --name gitops-argocd
${KIND_CMD} load docker-image event-processor:latest --name gitops-argocd
${KIND_CMD} load docker-image dashboard:latest --name gitops-argocd

echo "All images built and loaded successfully!"
