#!/bin/bash

# Run demo workload so Prometheus/Grafana dashboard metrics are non-zero

set -euo pipefail

echo "Deploying demo workload for dashboard metrics..."
kubectl create deployment demo-metrics --image=nginx:alpine --replicas=3 --dry-run=client -o yaml | \
  kubectl set resources -f - --requests=cpu=50m,memory=64Mi --limits=cpu=100m,memory=128Mi --local -o yaml | \
  kubectl apply -f -

echo "Waiting for demo pods to be Running..."
kubectl wait --for=condition=Ready pod -l app=demo-metrics --timeout=120s 2>/dev/null || true

echo "Waiting for metrics to be available (metrics-server)..."
sleep 15
if kubectl top pods -l app=demo-metrics 2>/dev/null | grep -q demo-metrics; then
  echo "✓ Pod metrics available (non-zero after a short delay):"
  kubectl top pods -l app=demo-metrics
else
  echo "Note: kubectl top may take 1-2 minutes. Run: kubectl top pods -l app=demo-metrics"
fi

echo ""
echo "Dashboard metrics will update with this workload. To view:"
echo "  Grafana:  kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80  (admin/admin)"
echo "  Prometheus: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "Demo deployment 'demo-metrics' is running. Delete with: kubectl delete deployment demo-metrics"
