#!/bin/bash
set -euo pipefail

echo "Running load test..."

# Port forward to log-ingest service
kubectl port-forward -n log-platform svc/log-ingest 8000:8000 &
PF_PID=$!

sleep 3

# Generate load
for i in {1..1000}; do
  curl -X POST http://localhost:8000/logs \
    -H "Content-Type: application/json" \
    -d "{
      \"level\": \"INFO\",
      \"service\": \"load-test\",
      \"message\": \"Test log message $i\"
    }" &
  
  if [ $((i % 100)) -eq 0 ]; then
    echo "Sent $i logs..."
    sleep 1
  fi
done

wait

kill $PF_PID

echo "✓ Load test complete"
echo "Check HPA status: kubectl get hpa -n log-platform"
echo "Check pod metrics: kubectl top pods -n log-platform"
