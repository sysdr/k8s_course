#!/bin/bash

set -euo pipefail

echo "Building Docker images..."

# Build services
docker build -t api-gateway:latest ./services/api-gateway
docker build -t order-service:latest ./services/order-service
docker build -t payment-service:latest ./services/payment-service

# Build frontend
docker build -t logging-dashboard:latest ./frontend

echo "All images built successfully!"
echo ""
echo "Images:"
echo "  - api-gateway:latest"
echo "  - order-service:latest"
echo "  - payment-service:latest"
echo "  - logging-dashboard:latest"
