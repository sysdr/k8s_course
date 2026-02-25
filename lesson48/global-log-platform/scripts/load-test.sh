#!/bin/bash
# load-test.sh — Generate realistic log ingestion load
set -euo pipefail
ENDPOINT="${1:-http://localhost:8000}"
DURATION="${2:-60}"
WORKERS="${3:-10}"

command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
python3 -c "import locust" 2>/dev/null || pip3 install locust --quiet

cat > /tmp/locustfile.py << 'LOCUST'
import json, random, time, uuid
from locust import HttpUser, task, between

SERVICES = ["auth-service","api-gateway","order-service","payment-service","inventory-service"]
LEVELS   = ["DEBUG","INFO","INFO","INFO","WARN","ERROR"]
MESSAGES = [
    "Request processed successfully",
    "Database query completed in {}ms".format(random.randint(1,500)),
    "Cache miss for key: user_{}".format(random.randint(1,10000)),
    "Circuit breaker state: CLOSED",
    "Retry attempt {} for upstream".format(random.randint(1,3)),
    "Connection pool exhausted",
]

class LogIngestionUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(8)
    def ingest_single(self):
        self.client.post("/ingest", json={
            "service":   random.choice(SERVICES),
            "level":     random.choice(LEVELS),
            "message":   random.choice(MESSAGES),
            "timestamp": time.time(),
            "trace_id":  str(uuid.uuid4()),
            "metadata":  {"host": f"pod-{random.randint(1,10)}"}
        })

    @task(2)
    def ingest_batch(self):
        events = [{
            "service":   random.choice(SERVICES),
            "level":     random.choice(LEVELS),
            "message":   random.choice(MESSAGES),
            "timestamp": time.time(),
            "trace_id":  str(uuid.uuid4()),
        } for _ in range(random.randint(10, 100))]
        self.client.post("/ingest/batch", json={"events": events})
LOCUST

locust -f /tmp/locustfile.py \
  --host="${ENDPOINT}" \
  --headless \
  --users="${WORKERS}" \
  --spawn-rate=2 \
  --run-time="${DURATION}s" \
  --csv=/tmp/load-test-results

echo "Load test complete. Results: /tmp/load-test-results_*.csv"
