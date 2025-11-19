#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="log-analytics"

echo "Deploying Log Analytics Platform..."

# Apply namespace first
kubectl apply -f "${PROJECT_ROOT}/k8s/base/namespace.yaml"

# Apply secrets (in production, use external secret management)
kubectl apply -f "${PROJECT_ROOT}/k8s/base/secrets.yaml"

# Apply ConfigMaps
kubectl apply -f "${PROJECT_ROOT}/k8s/base/configmap.yaml"

# Apply RBAC
kubectl apply -f "${PROJECT_ROOT}/k8s/base/rbac.yaml"

# Apply infrastructure (Postgres, Redis, Kafka)
kubectl apply -f "${PROJECT_ROOT}/k8s/base/infrastructure.yaml"

# Wait for infrastructure
echo "Waiting for infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=60s || true
kubectl wait --for=condition=ready pod -l app=kafka -n $NAMESPACE --timeout=120s || true

# Apply services
kubectl apply -f "${PROJECT_ROOT}/k8s/base/services.yaml"

# Apply deployments
kubectl apply -f "${PROJECT_ROOT}/k8s/base/deployments.yaml"

# Apply HPA
kubectl apply -f "${PROJECT_ROOT}/k8s/base/hpa.yaml"

# Apply PDB
kubectl apply -f "${PROJECT_ROOT}/k8s/base/pdb.yaml"

# Apply Network Policies
kubectl apply -f "${PROJECT_ROOT}/k8s/base/network-policies.yaml"

echo "Waiting for deployments..."
kubectl rollout status deployment/log-collector -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/log-processor -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/log-api -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=120s

echo "Deployment complete!"
kubectl get pods -n $NAMESPACE
