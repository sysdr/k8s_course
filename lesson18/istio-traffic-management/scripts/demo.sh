#!/bin/bash
set -euo pipefail

API_URL="${API_GATEWAY_URL:-http://localhost:30080}"

echo "=== Istio Traffic Management Demo ==="
echo ""

# Generate traffic to different versions
for i in {1..20}; do
    echo "Request $i..."
    curl -s "${API_URL}/api/v1/status" \
        -H "X-User-Id: demo-user-$i" \
        -H "X-Tier: free" | jq -r '.version // "unknown"' || echo "Request failed"
    sleep 0.5
done

echo ""
echo "=== Processing requests ==="
for i in {1..10}; do
    echo "Processing request $i..."
    curl -s -X POST "${API_URL}/api/v1/process" \
        -H "Content-Type: application/json" \
        -H "X-User-Id: demo-user-$i" \
        -H "X-Tier: premium" \
        -d "{\"request_id\": $i}" | jq -r '.version // "unknown"' || echo "Request failed"
    sleep 0.3
done

echo ""
echo "=== Fetching data ==="
for item in item-1 item-2 item-3 item-4 item-5; do
    echo "Fetching $item..."
    curl -s "${API_URL}/api/v1/data/$item" \
        -H "X-User-Id: demo-user" \
        -H "X-Tier: enterprise" | jq -r '.version // "unknown"' || echo "Request failed"
    sleep 0.2
done

echo ""
echo "Demo completed! Check dashboard for metrics."
