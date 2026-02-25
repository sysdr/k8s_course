#!/bin/bash
# build.sh — Build and load all service images into kind clusters
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR}/.."

SERVICES=("log-ingestion" "log-processor" "aggregator")
CLUSTERS=("us-east" "eu-west")

for svc in "${SERVICES[@]}"; do
  echo "Building ${svc}..."
  docker build -t "${svc}:latest" "${ROOT}/services/${svc}/"
  for cluster in "${CLUSTERS[@]}"; do
    echo "  Loading ${svc} into kind-${cluster}..."
    kind load docker-image "${svc}:latest" --name "${cluster}"
  done
done

echo "Building frontend..."
docker build -t log-dashboard:latest "${ROOT}/frontend/"
for cluster in "${CLUSTERS[@]}"; do
  kind load docker-image log-dashboard:latest --name "${cluster}"
done

echo "✓ All images built and loaded"
