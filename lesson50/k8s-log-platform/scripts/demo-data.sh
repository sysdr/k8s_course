#!/bin/bash
# Send sample log events to ingestion API so dashboard shows non-zero metrics.
set -euo pipefail
INGEST_URL="${INGEST_URL:-http://localhost:8000}"
COUNT="${DEMO_COUNT:-50}"
echo "Sending $COUNT sample events to $INGEST_URL ..."
for i in $(seq 1 "$COUNT"); do
  curl -sS -X POST "${INGEST_URL}/ingest" -H "Content-Type: application/json" -d "{
    \"service\": \"demo-service\",
    \"level\": \"INFO\",
    \"message\": \"Demo log event #$i for dashboard metrics\"
  }" >/dev/null || true
done
echo "Sending batch of 20 events..."
curl -sS -X POST "${INGEST_URL}/ingest/batch" -H "Content-Type: application/json" -d "{
  \"events\": [
    {\"service\": \"api-gateway\", \"level\": \"INFO\", \"message\": \"Request completed\"},
    {\"service\": \"auth-service\", \"level\": \"DEBUG\", \"message\": \"Token validated\"},
    {\"service\": \"payment-service\", \"level\": \"WARN\", \"message\": \"Retry attempt 2\"},
    {\"service\": \"order-service\", \"level\": \"ERROR\", \"message\": \"Inventory check failed\"}
  ]
}" >/dev/null || true
echo "✅ Demo data sent. Refresh dashboard at http://localhost:3000"
