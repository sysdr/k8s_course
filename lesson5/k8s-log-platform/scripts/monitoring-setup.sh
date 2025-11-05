#!/bin/bash
set -euo pipefail

echo "Setting up monitoring stack..."

kubectl port-forward -n log-platform svc/prometheus 9090:9090 &
kubectl port-forward -n log-platform svc/grafana 3000:3000 &
kubectl port-forward -n log-platform svc/jaeger-query 16686:16686 &

echo "Monitoring endpoints:"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (admin/admin123)"
echo "- Jaeger: http://localhost:16686"
echo ""
echo "Press Ctrl+C to stop port forwarding"
wait
