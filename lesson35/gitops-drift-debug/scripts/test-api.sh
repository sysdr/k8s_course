#!/bin/bash
set -euo pipefail

echo "Testing API endpoints and creating drift events..."

# Port forward in background
kubectl port-forward -n production svc/api-service 8000:8000 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health check failed"

# Create drift events with classification
echo ""
echo "2. Creating drift events with classification..."
curl -s -X POST http://localhost:8000/api/v1/drift-events \
  -H 'Content-Type: application/json' \
  -d '{"resource_type":"Deployment","resource_name":"worker","namespace":"production","git_sha":"c0ffee000","live_sha":"deadbeef0","user":"engineer@company.com","drift_type":"Intentional","drift_risk_level":"Medium","change_description":"Manual kubectl scale from 2 to 8 replicas during traffic spike"}' | python3 -m json.tool || echo "Failed to create drift event"

curl -s -X POST http://localhost:8000/api/v1/drift-events \
  -H 'Content-Type: application/json' \
  -d '{"resource_type":"Deployment","resource_name":"api-service","namespace":"production","git_sha":"abc123","live_sha":"def456","user":"admin@company.com","drift_type":"Accidental","drift_risk_level":"Low","change_description":"Configuration change not committed to Git"}' | python3 -m json.tool || echo "Failed to create drift event"

# Get drift events
echo ""
echo "3. Retrieving drift events..."
curl -s http://localhost:8000/api/v1/drift-events | python3 -m json.tool || echo "Failed to get drift events"

# Get deployments
echo ""
echo "4. Getting deployments..."
curl -s http://localhost:8000/api/v1/deployments | python3 -m json.tool || echo "Failed to get deployments"

# Check metrics
echo ""
echo "5. Checking Prometheus metrics..."
curl -s http://localhost:8000/metrics | grep -E '(api_requests_total|drift_events_total)' | head -10

# Cleanup
kill $PF_PID 2>/dev/null || true

echo ""
echo "Test completed!"
