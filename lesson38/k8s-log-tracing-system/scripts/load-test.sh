#!/bin/bash
set -euo pipefail
# load-test.sh — generate realistic ingest traffic using curl + sleep loop.
# For production-grade load testing, replace with k6 or Locust (see tests/).

INGEST_URL="${1:-http://localhost:8000/ingest}"
CONCURRENCY=10
DURATION=60   # seconds
INTERVAL=0.1  # seconds between requests per worker

SEVERITIES=("DEBUG" "INFO" "WARN" "ERROR" "FATAL")
SERVICES=("auth-svc" "order-svc" "payment-svc" "notification-svc" "api-gateway")

worker() {
  local id=$1
  local end_time=$(( $(date +%s) + DURATION ))
  local count=0
  while [[ $(date +%s) -lt $end_time ]]; do
    local sev=${SEVERITIES[$((RANDOM % ${#SEVERITIES[@]}))]}
    local svc=${SERVICES[$((RANDOM % ${#SERVICES[@]}))]}
    curl -s -X POST "${INGEST_URL}" \
      -H "Content-Type: application/json" \
      -d "{\"severity\":\"${sev}\",\"service\":\"${svc}\",\"message\":\"Load test event #${count} from worker ${id}\",\"metadata\":{\"worker\":${id}}}" \
      > /dev/null
    count=$((count + 1))
    sleep "${INTERVAL}"
  done
  echo "Worker ${id}: sent ${count} events"
}

echo "=== Starting load test: ${CONCURRENCY} workers for ${DURATION}s → ${INGEST_URL}"
for i in $(seq 1 $CONCURRENCY); do
  worker $i &
done
wait
echo "=== Load test complete."
