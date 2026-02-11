#!/bin/bash
set -euo pipefail
# build.sh — build all Docker images locally, tag for kind/minikube.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR}/.."

SERVICES=("log-ingestor" "log-processor" "analytics-service" "frontend")

for svc in "${SERVICES[@]}"; do
  echo "Building ${svc} …"
  docker build -t "${svc}:latest" "${ROOT}/src/${svc}"
done

echo ""
echo "All images built successfully."
echo "Load into kind:  kind load docker-image log-ingestor:latest log-processor:latest analytics-service:latest frontend:latest"
