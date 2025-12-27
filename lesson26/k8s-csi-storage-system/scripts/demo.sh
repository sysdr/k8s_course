#!/bin/bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:30080}"

echo "Running demo: Sending sample log entries..."

for i in {1..10}; do
    curl -X POST "${API_URL}/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"level\": \"INFO\",
            \"message\": \"Sample log entry $i\",
            \"source\": \"demo-script\"
        }" || true
    sleep 1
done

echo "Demo completed. Check dashboard at http://localhost:30000"
