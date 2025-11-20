#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check for kind
if ! command -v kind &> /dev/null; then
    echo "Installing kind..."
    GO111MODULE="on" go install sigs.k8s.io/kind@latest
fi

# Create cluster
kind create cluster --name health-probes --config - <<EOL
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOL

# Load images
kind load docker-image log-collector:latest --name health-probes
kind load docker-image log-processor:latest --name health-probes
kind load docker-image analytics-api:latest --name health-probes
kind load docker-image frontend:latest --name health-probes

echo "Cluster setup complete"
kubectl cluster-info
