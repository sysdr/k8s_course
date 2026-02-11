#!/bin/bash
# Stop all port-forwards

echo "Stopping all port-forwards..."
pkill -f "kubectl port-forward.*monitoring" 2>/dev/null && echo "✓ Port-forwards stopped" || echo "No port-forwards running"
