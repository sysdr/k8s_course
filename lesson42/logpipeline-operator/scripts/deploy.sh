#!/bin/bash

set -euo pipefail

echo "Deploying LogPipeline Operator system..."

# Create namespaces
kubectl create namespace logging-system --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -

# Deploy CRDs
echo "Deploying CRDs..."
kubectl apply -f k8s/crds/

# Deploy operator RBAC and deployment
echo "Deploying operator..."
kubectl apply -f k8s/operator/

# Wait for operator to be ready
echo "Waiting for operator to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/logpipeline-operator -n logging-system

# Deploy infrastructure
echo "Deploying infrastructure (Kafka, Redis, Elasticsearch)..."
kubectl apply -f k8s/base/kafka.yaml
kubectl apply -f k8s/base/redis.yaml
kubectl apply -f k8s/base/elasticsearch.yaml

# Deploy monitoring
echo "Deploying monitoring stack..."
kubectl apply -f k8s/monitoring/

# Deploy example LogPipeline
echo "Deploying example LogPipeline..."
kubectl apply -f k8s/base/example-logpipeline.yaml

echo "Deployment complete!"
echo "Check status with: kubectl get logpipelines -n logging"
