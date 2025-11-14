#!/bin/bash
set -euo pipefail

NAMESPACE="log-processing"
DURATION=${1:-60}  # Default 60 seconds
RPS=${2:-100}      # Default 100 requests per second

echo "Running load test for ${DURATION}s at ${RPS} RPS..."

# Port forward in background
kubectl port-forward svc/ingestion-service 8000:8000 -n $NAMESPACE &
PF_PID=$!
sleep 3

# Generate load
python3 << PYTHON
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
SERVICES = ['api-gateway', 'user-service', 'order-service', 'payment-service']
URL = 'http://localhost:8000/api/v1/ingest'

def send_log():
    try:
        payload = {
            'level': random.choice(LEVELS),
            'service': random.choice(SERVICES),
            'message': f'Test log message at {datetime.utcnow().isoformat()}'
        }
        response = requests.post(URL, json=payload, timeout=5)
        return response.status_code == 202
    except Exception as e:
        return False

start_time = time.time()
duration = ${DURATION}
rps = ${RPS}
interval = 1.0 / rps

success = 0
failure = 0

with ThreadPoolExecutor(max_workers=10) as executor:
    while time.time() - start_time < duration:
        future = executor.submit(send_log)
        if future.result(timeout=5):
            success += 1
        else:
            failure += 1
        time.sleep(interval)

print(f"\nLoad test complete:")
print(f"  Duration: {duration}s")
print(f"  Target RPS: {rps}")
print(f"  Success: {success}")
print(f"  Failure: {failure}")
print(f"  Actual RPS: {success / duration:.2f}")
PYTHON

# Kill port forward
kill $PF_PID

echo "✓ Load test complete"
