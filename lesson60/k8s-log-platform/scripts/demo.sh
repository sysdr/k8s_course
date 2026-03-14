#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
API_URL="${API_URL:-http://localhost:8000}"
echo "Sending demo logs to $API_URL..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -s -X POST "$API_URL/logs" -H "Content-Type: application/json" -d "{\"level\": \"INFO\", \"message\": \"Demo log message $i\", \"service\": \"demo-script\"}" && echo " OK" || echo " (retry $i)"
  sleep 0.3
done
echo "Demo logs sent. Dashboard should update (select service 'demo-script' or 'All Services')."
