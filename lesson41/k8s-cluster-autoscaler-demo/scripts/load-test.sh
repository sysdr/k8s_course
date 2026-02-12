#!/bin/bash
set -euo pipefail

INGESTION_URL=${1:-"http://localhost:8000"}
DURATION=${2:-60}
RATE=${3:-100}

echo "Starting load test..."
echo "Target: $INGESTION_URL"
echo "Duration: ${DURATION}s"
echo "Rate: ${RATE} requests/second"

python3 load-tests/locust_test.py --headless \
  --users $RATE \
  --spawn-rate 10 \
  --run-time ${DURATION}s \
  --host $INGESTION_URL
