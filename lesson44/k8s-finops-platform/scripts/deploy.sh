#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"

echo "Deploying FinOps platform to Kubernetes..."

# Apply namespaces
kubectl apply -f kubernetes/base/namespaces/

# Apply quotas
kubectl apply -f kubernetes/base/quotas/

# Deploy applications
kubectl apply -f kubernetes/applications/log-ingest/
kubectl apply -f kubernetes/applications/cost-analyzer/
kubectl apply -f kubernetes/applications/frontend/

# Deploy autoscaling
kubectl apply -f kubernetes/autoscaling/

# Deploy monitoring
kubectl apply -f kubernetes/monitoring/prometheus/
kubectl apply -f kubernetes/monitoring/grafana/

echo "Deployment complete!"
echo "Run 'kubectl get pods -A' to check status"
