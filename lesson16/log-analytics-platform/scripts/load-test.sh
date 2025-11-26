#!/bin/bash
set -euo pipefail

echo "Running load test against Log Analytics Platform..."

API_URL="${1:-http://localhost:8080}"

echo "Testing against: $API_URL"
echo ""

# Test log ingestion
echo "1. Testing log ingestion endpoint..."
for i in {1..50}; do
  curl -s -X POST "$API_URL/api/ingest" \
    -H "Content-Type: application/json" \
    -d "{
      \"level\": \"INFO\",
      \"message\": \"Load test log $i\",
      \"source\": \"load-test\"
    }" > /dev/null &
done

wait
echo "✓ Sent 50 log ingestion requests"

# Test query endpoint
echo "2. Testing query endpoint..."
for i in {1..100}; do
  curl -s "$API_URL/api/query?limit=10" > /dev/null &
done

wait
echo "✓ Sent 100 query requests"

# Test analytics endpoint
echo "3. Testing analytics endpoint..."
for i in {1..50}; do
  curl -s "$API_URL/api/analytics/summary" > /dev/null &
done

wait
echo "✓ Sent 50 analytics requests"

echo ""
echo "Load test complete! Check metrics:"
echo "  kubectl port-forward -n monitoring svc/prometheus 9090:9090"
