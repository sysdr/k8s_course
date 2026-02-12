#!/bin/bash

set -euo pipefail

echo "Running load test..."

# Simple load test using curl in a loop
COLLECTOR_URL=$(kubectl get svc -n logging -l component=collector -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')

for i in {1..1000}; do
  curl -X POST "http://${COLLECTOR_URL}:8080/logs" \
    -H "Content-Type: application/json" \
    -d "{\"timestamp\":\"$(date -Iseconds)\",\"level\":\"INFO\",\"message\":\"Test log $i\",\"pod_name\":\"test-pod\",\"namespace\":\"test\",\"container\":\"app\"}" &
  
  if (( i % 100 == 0 )); then
    echo "Sent $i requests..."
    wait
  fi
done

wait
echo "Load test complete!"
