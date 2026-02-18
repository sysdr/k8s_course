#!/bin/bash
set -euo pipefail

echo "🔥 Running load test against log ingestion service..."

# Port forward to service
kubectl port-forward -n log-platform svc/log-ingestion 8000:8000 &
PF_PID=$!
sleep 5

# Generate load
echo "Sending 1000 log entries..."
for i in {1..1000}; do
    curl -s -X POST http://localhost:8000/api/v1/logs \
        -H "Content-Type: application/json" \
        -d "{
            \"level\": \"INFO\",
            \"message\": \"Test log message $i\",
            \"source\": \"load-test\"
        }" > /dev/null &
    
    if [ $((i % 100)) -eq 0 ]; then
        echo "Sent $i requests..."
    fi
done

wait

echo "✅ Load test complete!"

# Cleanup
kill $PF_PID 2>/dev/null || true

# Show metrics
echo ""
echo "📊 Checking metrics..."
kubectl exec -n log-platform \
    $(kubectl get pods -n log-platform -l app=log-ingestion -o jsonpath='{.items[0].metadata.name}') \
    -- curl -s http://localhost:8000/metrics | grep log_ingestion_total
