#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

LOG_COLLECTOR_URL="${LOG_COLLECTOR_URL:-http://localhost:30080}"
echo "Sending demo traffic to $LOG_COLLECTOR_URL (set LOG_COLLECTOR_URL to override)..."

for i in $(seq 1 30); do
  curl -s -X POST "$LOG_COLLECTOR_URL/api/v1/logs" \
    -H "Content-Type: application/json" \
    -d "[
      {\"level\":\"INFO\",\"service\":\"api\",\"message\":\"Demo request $i\",\"metadata\":{}},
      {\"level\":\"WARNING\",\"service\":\"worker\",\"message\":\"Demo warning $i\",\"metadata\":{}},
      {\"level\":\"ERROR\",\"service\":\"scheduler\",\"message\":\"Demo error $i\",\"metadata\":{}}
    ]" > /dev/null || true
  sleep 0.5
done

echo "Demo traffic sent. Dashboard and metrics should update (refresh or wait for poll)."
