#!/bin/bash
set -euo pipefail

API_URL="${API_GATEWAY_URL:-http://localhost:30080}"
REQUESTS="${REQUESTS:-100}"
CONCURRENT="${CONCURRENT:-10}"

echo "Running load test..."
echo "API Gateway URL: $API_URL"
echo "Total requests: $REQUESTS"
echo "Concurrent: $CONCURRENT"
echo ""

if command -v ab &> /dev/null; then
    ab -n "$REQUESTS" -c "$CONCURRENT" \
        -H "X-User-Id: load-test-user" \
        -H "X-Tier: premium" \
        "${API_URL}/api/v1/status"
else
    echo "Apache Bench (ab) not found. Using curl for basic test..."
    for i in $(seq 1 "$REQUESTS"); do
        curl -s -o /dev/null -w "%{http_code}\n" \
            -H "X-User-Id: load-test-user-$i" \
            -H "X-Tier: premium" \
            "${API_URL}/api/v1/status" &
        if [ $((i % CONCURRENT)) -eq 0 ]; then
            wait
        fi
    done
    wait
    echo "Load test completed!"
fi
