#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Deploying runtime security system..."

# Create namespace
kubectl apply -f "${BASE_DIR}/k8s/base/namespace.yaml"

# Deploy services
kubectl apply -f "${BASE_DIR}/k8s/services/"

# Deploy Falco
kubectl apply -f "${BASE_DIR}/k8s/falco/"

# Apply security policies
kubectl apply -f "${BASE_DIR}/k8s/security-policies/"

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/security-event-processor \
  deployment/incident-response-controller \
  deployment/security-dashboard \
  -n runtime-security

echo "✓ Deployment complete!"
echo ""
echo "Access the dashboard:"
echo "  kubectl port-forward -n runtime-security svc/security-dashboard 8080:80"
echo "  Open: http://localhost:8080"
