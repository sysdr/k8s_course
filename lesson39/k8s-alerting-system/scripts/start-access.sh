#!/bin/bash
# Start port-forwards for accessing services on localhost
# This is required for kind clusters where NodePorts don't work on localhost

set -e

echo "Starting port-forwards for services..."
echo ""

# Kill any existing port-forwards
pkill -f "kubectl port-forward.*monitoring" 2>/dev/null || true
sleep 1

# Start port-forwards
kubectl port-forward -n monitoring svc/grafana 30300:3000 >/dev/null 2>&1 &
GRAFANA_PF=$!
echo "Grafana port-forward started (PID: $GRAFANA_PF)"

kubectl port-forward -n monitoring svc/prometheus 30090:9090 >/dev/null 2>&1 &
PROMETHEUS_PF=$!
echo "Prometheus port-forward started (PID: $PROMETHEUS_PF)"

kubectl port-forward -n monitoring svc/alertmanager-external 30903:9093 >/dev/null 2>&1 &
ALERTMANAGER_PF=$!
echo "Alertmanager port-forward started (PID: $ALERTMANAGER_PF)"

sleep 3

echo ""
echo "✓ All port-forwards active!"
echo ""
echo "Services are now accessible at:"
echo "  Grafana:      http://localhost:30300 (admin/admin)"
echo "  Prometheus:   http://localhost:30090"
echo "  Alertmanager: http://localhost:30903"
echo ""
echo "To stop port-forwards, run: ./scripts/stop-access.sh"
echo "Or: pkill -f 'kubectl port-forward'"
