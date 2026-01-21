#!/bin/bash

set -euo pipefail

echo "=== Testing Services ==="
echo ""

echo "1. Testing Auth Service Login (direct):"
AUTH_RESPONSE=$(curl -s -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
echo "$AUTH_RESPONSE"
TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  echo "Failed to get token from auth service"
  exit 1
fi

echo ""
echo "2. Testing API Gateway Login:"
GATEWAY_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
echo "$GATEWAY_RESPONSE"
GATEWAY_TOKEN=$(echo "$GATEWAY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$GATEWAY_TOKEN" ]; then
  echo "Failed to get token from API Gateway"
  exit 1
fi

echo ""
echo "3. Testing Analytics Endpoint:"
ANALYTICS=$(curl -s http://localhost:8000/analytics/summary \
  -H "Authorization: Bearer $GATEWAY_TOKEN")
echo "$ANALYTICS"

echo ""
echo "4. Testing Metrics Endpoints:"
echo "API Gateway metrics (first 5 lines):"
curl -s http://localhost:8000/metrics | head -5
echo ""
echo "Auth Service metrics (first 5 lines):"
curl -s http://localhost:8001/metrics | head -5

echo ""
echo "=== All Tests Completed ==="
