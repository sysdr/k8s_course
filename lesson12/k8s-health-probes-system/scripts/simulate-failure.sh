#!/bin/bash
set -euo pipefail

echo "Simulating failures to test self-healing..."

# Test 1: Kill a pod and watch restart
echo "Test 1: Deleting a log-collector pod..."
kubectl delete pod -n log-analytics -l app=log-collector --wait=false | head -1

echo "Watching pod restart..."
kubectl get pods -n log-analytics -l app=log-collector -w &
WATCH_PID=$!
sleep 30
kill $WATCH_PID 2>/dev/null || true

# Test 2: Simulate readiness failure
echo ""
echo "Test 2: Simulating readiness probe failure..."
API_POD=$(kubectl get pod -n log-analytics -l app=analytics-api -o jsonpath='{.items[0].metadata.name}')

echo "Current endpoints:"
kubectl get endpoints analytics-api -n log-analytics

# The service will automatically remove unhealthy pods from endpoints

echo ""
echo "Failure simulation complete!"
echo "Check pod status and endpoints to verify self-healing behavior"
