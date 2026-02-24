#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Cluster A ingestion URL (docker-compose: 8000, or set CLUSTER_A_URL / LoadBalancer IP)
CLUSTER_A_URL="${CLUSTER_A_URL:-http://localhost:8000}"
COUNT="${DEMO_LOG_COUNT:-50}"

echo "Sending $COUNT demo logs to $CLUSTER_A_URL so dashboard metrics update..."

for i in $(seq 1 "$COUNT"); do
  curl -s -X POST "$CLUSTER_A_URL/ingest" \
    -H "Content-Type: application/json" \
    -d "{\"service\": \"demo-service\", \"level\": \"INFO\", \"message\": \"Demo log message $i\", \"trace_id\": \"demo-$i\"}" \
    >/dev/null || true
done

echo "Demo logs sent. Refresh the dashboard to see updated metrics (processed count, stats)."
