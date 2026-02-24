#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"

echo "Running load test to generate cost data..."

kubectl port-forward -n prod-logging svc/log-ingest-service 8000:8000 &
PF_PID=$!

sleep 5

# Generate test load
for i in {1..1000}; do
    curl -X POST http://localhost:8000/ingest \
        -H "Content-Type: application/json" \
        -d '{
            "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
            "source": "load-test",
            "severity": "info",
            "message": "Test log entry '$i'",
            "metadata": {"test": true}
        }' &
    
    if [ $((i % 100)) -eq 0 ]; then
        echo "Sent $i requests..."
        sleep 1
    fi
done

wait

kill $PF_PID

echo "Load test complete!"
