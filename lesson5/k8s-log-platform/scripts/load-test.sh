#!/bin/bash
set -euo pipefail

echo "Running load test..."

kubectl port-forward -n log-platform svc/log-ingestion 8000:8000 &
PF_PID=$!

sleep 5

# Install Apache Bench if not available
if ! command -v ab &> /dev/null; then
    echo "Installing Apache Bench..."
    apt-get update && apt-get install -y apache2-utils || brew install apache-bench
fi

# Run load test
echo "Sending 10000 requests with 100 concurrent connections..."
ab -n 10000 -c 100 -p load-test-data.json -T application/json http://localhost:8000/api/v1/logs

kill $PF_PID

echo "Load test complete!"
