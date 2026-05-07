#!/bin/bash
# Monitor DNS resolution performance from inside the container.
# In production, integrate with Prometheus via custom metrics endpoint.

CONTAINER="${1:-lesson65-api}"
TARGET="${2:-processor}"
ITERATIONS="${3:-10}"

echo "DNS resolution latency test: ${TARGET} from ${CONTAINER} (${ITERATIONS} iterations)"
echo ""

for i in $(seq 1 "${ITERATIONS}"); do
  START=$(date +%s%N)
  docker exec "${CONTAINER}" nslookup "${TARGET}" 127.0.0.11 > /dev/null 2>&1
  END=$(date +%s%N)
  LATENCY_MS=$(( (END - START) / 1000000 ))
  echo "  Iteration ${i}: ${LATENCY_MS}ms"
  sleep 0.5
done
