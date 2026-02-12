#!/bin/bash

echo "Stopping all port-forwards..."

pkill -f "kubectl port-forward.*frontend" 2>/dev/null && echo "✓ Stopped frontend port-forward" || echo "✗ Frontend port-forward not running"
pkill -f "kubectl port-forward.*grafana" 2>/dev/null && echo "✓ Stopped Grafana port-forward" || echo "✗ Grafana port-forward not running"
pkill -f "kubectl port-forward.*prometheus" 2>/dev/null && echo "✓ Stopped Prometheus port-forward" || echo "✗ Prometheus port-forward not running"

echo "Done."
