#!/bin/bash

set -euo pipefail

DURATION=${1:-300}
RATE=${2:-10}

echo "Running load test..."
echo "Duration: ${DURATION}s"
echo "Rate: ${RATE} req/s"

# Get Istio ingress endpoint
INGRESS_HOST=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$INGRESS_HOST" ]; then
    INGRESS_HOST="localhost"
fi

# Run load test using Python
python3 << PYTHON_EOF
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor
import json

url = "http://${INGRESS_HOST}/orders"
duration = ${DURATION}
rate = ${RATE}

def create_order():
    order = {
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "items": [
            {
                "product_id": f"PROD-{random.randint(1, 100)}",
                "quantity": random.randint(1, 5),
                "price": round(random.uniform(10, 100), 2)
            }
        ]
    }
    try:
        response = requests.post(url, json=order, timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False

start_time = time.time()
success = 0
failure = 0

with ThreadPoolExecutor(max_workers=10) as executor:
    while time.time() - start_time < duration:
        futures = [executor.submit(create_order) for _ in range(rate)]
        results = [f.result() for f in futures]
        success += sum(results)
        failure += len(results) - sum(results)
        
        if int(time.time() - start_time) % 10 == 0:
            print(f"Progress: {int(time.time() - start_time)}s - Success: {success}, Failure: {failure}")
        
        time.sleep(1)

print(f"\nLoad test complete!")
print(f"Total requests: {success + failure}")
print(f"Success: {success} ({success/(success+failure)*100:.1f}%)")
print(f"Failure: {failure} ({failure/(success+failure)*100:.1f}%)")
