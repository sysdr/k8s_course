#!/bin/bash

set -euo pipefail

echo "Building container images..."

# Build order service
echo "Building order-service:v1..."
docker build -t order-service:v1 ./services/order-service

echo "Building order-service:v2 (canary version with higher latency)..."
docker build -t order-service:v2 \
  --build-arg VERSION=v2 \
  --build-arg LATENCY_MS=100 \
  ./services/order-service

# Build payment gateway
echo "Building payment-gateway:v1..."
docker build -t payment-gateway:v1 ./services/payment-gateway

# Build frontend
echo "Building frontend:v1..."
docker build -t progressive-delivery-frontend:v1 ./frontend

# Load images into kind
echo "Loading images into kind cluster..."
kind load docker-image order-service:v1 --name progressive-delivery
kind load docker-image order-service:v2 --name progressive-delivery
kind load docker-image payment-gateway:v1 --name progressive-delivery
kind load docker-image progressive-delivery-frontend:v1 --name progressive-delivery

echo "✓ All images built and loaded!"
