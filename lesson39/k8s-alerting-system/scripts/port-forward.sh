#!/bin/bash
# Port forwarding script for kind cluster services
# Run this in the background to access services on localhost

set -e

echo "Setting up port-forwarding for services..."
echo "Press Ctrl+C to stop all port-forwards"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all port-forwards..."
    kill $GRAFANA_PF $PROMETHEUS_PF $ALERTMANAGER_PF 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start port-forwards in background
kubectl port-forward -n monitoring svc/grafana 30300:3000 >/dev/null 2>&1 &
GRAFANA_PF=$!

kubectl port-forward -n monitoring svc/prometheus 30090:9090 >/dev/null 2>&1 &
PROMETHEUS_PF=$!

kubectl port-forward -n monitoring svc/alertmanager-external 30903:9093 >/dev/null 2>&1 &
ALERTMANAGER_PF=$!

sleep 2

echo "✓ Port-forwarding active!"
echo ""
echo "Access services at:"
echo "  Grafana:      http://localhost:30300 (admin/admin)"
echo "  Prometheus:   http://localhost:30090"
echo "  Alertmanager: http://localhost:30903"
echo ""
echo "Port-forwards running in background. Press Ctrl+C to stop."

# Wait for user interrupt
wait
