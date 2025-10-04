#!/bin/bash
set -euo pipefail

API_URL="${1:-http://localhost:8000}"
NUM_REQUESTS="${2:-1000}"

echo "Running load test against: $API_URL"
echo "Number of requests: $NUM_REQUESTS"

for i in $(seq 1 $NUM_REQUESTS); do
    curl -s -X POST "$API_URL/logs" \
        -H "Content-Type: application/json" \
        -d "{
            \"service\": \"load-test\",
            \"level\": \"INFO\",
            \"message\": \"Load test message $i\"
        }" > /dev/null
    
    if [ $((i % 100)) -eq 0 ]; then
        echo "Sent $i requests..."
    fi
done

echo "✓ Load test complete! Sent $NUM_REQUESTS requests"
