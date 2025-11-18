#!/bin/bash
set -euo pipefail

echo "Running load test against log analytics platform..."

API_URL="${1:-http://localhost:30080}"
DURATION="${2:-60}"
RATE="${3:-100}"

echo "Target: ${API_URL}"
echo "Duration: ${DURATION}s"
echo "Rate: ${RATE} requests/second"

# Generate test logs
for i in $(seq 1 $((DURATION * RATE))); do
    curl -s -X POST "${API_URL}/api/v1/logs" \
        -H "Content-Type: application/json" \
        -d "{
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
            \"level\": \"INFO\",
            \"service\": \"load-test\",
            \"message\": \"Load test message ${i}\"
        }" &
    
    # Control request rate
    if (( i % RATE == 0 )); then
        sleep 1
        echo "Sent ${i} requests..."
    fi
done

wait
echo "Load test complete!"
