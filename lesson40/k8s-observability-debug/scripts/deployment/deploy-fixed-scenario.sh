#!/bin/bash
set -euo pipefail

echo "✅ Deploying FIXED observability scenario..."

# Deploy applications
kubectl apply -f k8s/base/applications/

# Deploy FIXED ServiceMonitor
kubectl apply -f k8s/overlays/fixed/servicemonitor-fixed.yaml

# Apply Prometheus rules
kubectl apply -f monitoring/prometheus/rules/

echo ""
echo "✅ Fixed scenario deployed!"
echo ""
echo "Expected behavior:"
echo "  1. Grafana shows live metrics"
echo "  2. Prometheus targets page shows healthy log-processor targets"
echo "  3. All diagnostic checks pass"
echo ""
echo "Verify with: python3 scripts/diagnostics/check-observability-stack.py"
