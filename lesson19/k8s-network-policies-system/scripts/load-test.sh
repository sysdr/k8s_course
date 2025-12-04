#!/bin/bash
set -euo pipefail

echo "Starting load test..."

API_URL=${1:-"http://localhost:8080"}

echo "Sending test logs to $API_URL/api/logs/ingest"

for i in {1..1000}; do
    curl -s -X POST "$API_URL/api/logs/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"level\": \"INFO\",
            \"service\": \"test-service-$((RANDOM % 10))\",
            \"message\": \"Test log entry $i\"
        }" > /dev/null
    
    if [ $((i % 100)) -eq 0 ]; then
        echo "Sent $i logs..."
    fi
done

echo "✓ Load test complete - 1000 logs sent"
