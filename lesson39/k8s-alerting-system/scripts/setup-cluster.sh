#!/bin/bash
set -e
echo "Setting up cluster..."
if command -v kind >/dev/null 2>&1; then
    kind create cluster --name alert-demo || true
    kind load docker-image log-ingestor:latest --name alert-demo
    kind load docker-image log-transformer:latest --name alert-demo
    kind load docker-image log-analyzer:latest --name alert-demo
elif command -v minikube >/dev/null 2>&1; then
    minikube start || true
    eval $(minikube docker-env)
else
    echo "Install kind or minikube"
    exit 1
fi
echo "✓ Cluster ready"
