#!/bin/bash
set -euo pipefail

API_URL="${1:-http://localhost:8080}"
DURATION="${2:-60}"
RATE="${3:-100}"

echo "Running load test against ${API_URL} for ${DURATION}s at ${RATE} req/s"

# Generate sample logs
for i in $(seq 1 $((DURATION * RATE))); do
    curl -s -X POST "${API_URL}/logs" \
        -H "Content-Type: application/json" \
        -d '{
            "level": "INFO",
            "service": "load-test",
            "message": "Test log message '"$i"'",
            "metadata": {"test_id": '"$i"'}
        }' &
    
    if (( i % RATE == 0 )); then
        sleep 1
    fi
done

wait
echo "Load test complete!"
