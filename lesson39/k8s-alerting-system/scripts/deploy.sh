#!/bin/bash
set -e
echo "Deploying..."
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/kafka.yaml
sleep 20
kubectl apply -f k8s/base/log-ingestor.yaml
kubectl apply -f k8s/base/log-transformer.yaml
kubectl apply -f k8s/base/log-analyzer.yaml
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/alertmanager.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
echo "✓ Deployed"
echo ""
echo "Access (for kind cluster, use port-forwarding):"
echo "  Run: ./scripts/port-forward.sh"
echo ""
echo "Or manually:"
echo "  Grafana:      kubectl port-forward -n monitoring svc/grafana 30300:3000"
echo "  Prometheus:   kubectl port-forward -n monitoring svc/prometheus 30090:9090"
echo "  Alertmanager: kubectl port-forward -n monitoring svc/alertmanager-external 30903:9093"
