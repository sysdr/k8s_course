#!/bin/bash
# Demo: send log traffic so dashboard shows non-zero metrics.
# Use with docker-compose: run from project root or pass INGEST_URL (default http://localhost:8000)
set -euo pipefail

INGEST_URL="${INGEST_URL:-http://localhost:8000}"
echo "🔥 Sending demo logs to $INGEST_URL (dashboard will update in a few seconds)..."

for i in $(seq 1 200); do
  level="INFO"
  [ $((i % 10)) -eq 0 ] && level="WARN"
  [ $((i % 25)) -eq 0 ] && level="ERROR"
  curl -s -X POST "$INGEST_URL/api/v1/logs" \
    -H "Content-Type: application/json" \
    -d "{\"level\": \"$level\", \"message\": \"Demo log message $i\", \"source\": \"demo\"}" > /dev/null &
  [ $((i % 50)) -eq 0 ] && echo "  Sent $i logs..." && wait
done
wait
echo "✅ Demo complete! Check dashboard at http://localhost:3000 (or port-forward port)"
