#!/bin/bash

set -euo pipefail

echo "Building Docker images..."

# Build services
cd services/product-service && docker build -t product-service:latest . && cd ../..
cd services/order-service && docker build -t order-service:latest . && cd ../..
cd services/payment-service && docker build -t payment-service:latest . && cd ../..
cd services/test-results-aggregator && docker build -t test-results-aggregator:latest . && cd ../..

# Build test runner
cd test-runner && docker build -t test-runner:latest . && cd ..

# Build frontend (optional)
# cd frontend && docker build -t frontend:latest . && cd ..

echo "✓ All images built successfully"
