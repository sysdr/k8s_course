#!/bin/bash

set -euo pipefail

echo "Fetching test results..."

# Port forward to aggregator
kubectl port-forward -n ecommerce svc/test-results-aggregator 8003:8003 &
PF_PID=$!
sleep 3

# Get summary
echo ""
echo "========================================"
echo "  Test Results Summary"
echo "========================================"
curl -s http://localhost:8003/api/v1/results/summary | jq .

echo ""
echo "========================================"
echo "  Detailed Results"
echo "========================================"
curl -s http://localhost:8003/api/v1/results | jq .

kill $PF_PID

echo ""
echo "To view in browser, run:"
echo "kubectl port-forward -n ecommerce svc/test-results-aggregator 8003:8003"
echo "Then visit: http://localhost:8003/api/v1/results"
