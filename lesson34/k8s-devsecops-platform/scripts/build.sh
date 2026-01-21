#!/bin/bash

set -euo pipefail

echo "Building container images..."

SERVICES=("api-gateway" "auth-service" "log-processor" "analytics-service")

for service in "${SERVICES[@]}"; do
    echo "Building $service..."
    docker build -t "$service:latest" "./services/$service"
done

echo "Building frontend..."
docker build -t "frontend:latest" "./frontend"

echo "Loading images to kind cluster..."
for service in "${SERVICES[@]}" frontend; do
    echo "Loading $service..."
    kind load docker-image "$service:latest" --name devsecops-cluster
done

echo "All images built and loaded successfully!"
