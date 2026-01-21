#!/bin/bash

set -euo pipefail

echo "=== Generating Demo Data ==="

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token obtained"

# Generate log entries
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/logs \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"level\":\"INFO\",\"message\":\"Demo log entry $i\",\"service\":\"demo-service\"}" > /dev/null
done

echo "Generated 10 log entries"

# Check log processor stats
echo ""
echo "=== Log Processor Stats ==="
curl -s http://localhost:8002/stats | python3 -m json.tool

echo ""
echo "=== Analytics Summary ==="
curl -s http://localhost:8000/analytics/summary \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== Metrics Summary ==="
echo "API Gateway requests:"
curl -s http://localhost:8000/metrics | grep 'api_gateway_requests_total' | grep -v '#'

echo ""
echo "Auth attempts:"
curl -s http://localhost:8001/metrics | grep 'auth_attempts_total' | grep -v '#'

echo ""
echo "Logs processed:"
curl -s http://localhost:8002/metrics | grep 'logs_processed_total' | grep -v '#'

echo ""
echo "=== Demo Data Generation Complete ==="
