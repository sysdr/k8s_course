#!/bin/bash
kubectl port-forward -n log-processing svc/log-ingestor 8080:8080 &
PF_PID=$!
sleep 2
for i in {1..50}; do
  curl -s -X POST http://localhost:8080/ingest \
    -H "Content-Type: application/json" \
    -d "{
      \"timestamp\": $(date +%s000),
      \"level\": \"ERROR\",
      \"service\": \"test-svc\",
      \"message\": \"Test error $i\"
    }"
  echo "Sent $i"
done
kill $PF_PID 2>/dev/null
echo "✓ Load test complete"
