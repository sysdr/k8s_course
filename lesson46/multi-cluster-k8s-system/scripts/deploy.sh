#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Building container images..."
docker build -t log-collector:latest ./services/log-collector
docker build -t log-processor:latest ./services/log-processor
docker build -t analytics-engine:latest ./services/analytics-engine
docker build -t dashboard:latest ./frontend

echo "Loading images into clusters..."
for cluster in cluster-us-west cluster-eu-west cluster-ap-southeast; do
  kind load docker-image log-collector:latest --name "$cluster"
  kind load docker-image log-processor:latest --name "$cluster"
  kind load docker-image analytics-engine:latest --name "$cluster"
  kind load docker-image dashboard:latest --name "$cluster"
done

echo "Applying Karmada policies..."
kubectl --context kind-control-plane apply -f karmada/policies/

echo "Deploying applications via Helm..."
helm upgrade --install multi-cluster-app ./helm/multi-cluster-app \
  --kube-context kind-control-plane \
  --namespace default \
  --create-namespace

echo "Deployment complete!"
echo "Access dashboard at: http://localhost:30080"
