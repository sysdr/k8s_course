#!/bin/bash
set -euo pipefail

echo "Starting port-forwarding for all services..."

# Kill any existing port-forwards
pkill -f "kubectl port-forward.*frontend" 2>/dev/null || true
pkill -f "kubectl port-forward.*grafana" 2>/dev/null || true
pkill -f "kubectl port-forward.*prometheus" 2>/dev/null || true

sleep 2

# Start port-forwards in background
echo "Starting frontend port-forward (8080)..."
kubectl port-forward -n log-platform svc/frontend 8080:80 > /tmp/frontend-pf.log 2>&1 &
FRONTEND_PID=$!

echo "Starting Grafana port-forward (3000)..."
kubectl port-forward -n log-platform svc/grafana 3000:3000 > /tmp/grafana-pf.log 2>&1 &
GRAFANA_PID=$!

echo "Starting Prometheus port-forward (9090)..."
kubectl port-forward -n log-platform svc/prometheus 9090:9090 > /tmp/prometheus-pf.log 2>&1 &
PROMETHEUS_PID=$!

sleep 3

# Verify they're running
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✓ Frontend port-forward running (PID: $FRONTEND_PID)"
else
    echo "✗ Frontend port-forward failed to start"
fi

if ps -p $GRAFANA_PID > /dev/null 2>&1; then
    echo "✓ Grafana port-forward running (PID: $GRAFANA_PID)"
else
    echo "✗ Grafana port-forward failed to start"
fi

if ps -p $PROMETHEUS_PID > /dev/null 2>&1; then
    echo "✓ Prometheus port-forward running (PID: $PROMETHEUS_PID)"
else
    echo "✗ Prometheus port-forward failed to start"
fi

echo ""
echo "Access URLs:"
echo "  Frontend:   http://localhost:8080"
echo "  Grafana:    http://localhost:3000 (admin/admin)"
echo "  Prometheus: http://localhost:9090"
echo ""
echo "Port-forwards are running in the background."
echo "To stop them, run: ./scripts/stop-port-forwards.sh"
