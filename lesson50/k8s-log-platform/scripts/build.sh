#!/bin/bash
set -euo pipefail
REGISTRY="${REGISTRY:-localhost:5001}"
TAG="${TAG:-latest}"

echo "Building service images..."

services=("log-ingestion" "log-processor" "log-query")
for svc in "${services[@]}"; do
  echo "Building $svc..."
  docker build -t "${REGISTRY}/${svc}:${TAG}" "services/${svc}/"
  docker push "${REGISTRY}/${svc}:${TAG}"
done

echo "Building frontend..."
docker build -t "${REGISTRY}/frontend:${TAG}" frontend/
docker push "${REGISTRY}/frontend:${TAG}"

echo "✅ All images built and pushed to ${REGISTRY}"
