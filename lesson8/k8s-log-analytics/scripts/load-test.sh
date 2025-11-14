#!/bin/bash
set -euo pipefail

echo "Running load test..."

cat > /tmp/load-test.py << 'PYEOF'
import requests
import random
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000/logs"

SERVICES = ["web-server", "api-gateway", "database", "cache", "queue"]
LEVELS = ["INFO", "WARNING", "ERROR", "DEBUG"]
MESSAGES = [
    "Request processed successfully",
    "Cache miss, fetching from database",
    "Database query executed",
    "User authentication successful",
    "Rate limit exceeded"
]

def send_log():
    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": random.choice(LEVELS),
        "service": random.choice(SERVICES),
        "message": random.choice(MESSAGES),
        "metadata": {
            "request_id": f"req-{random.randint(1000, 9999)}",
            "user_id": f"user-{random.randint(1, 100)}"
        }
    }
    
    try:
        response = requests.post(API_URL, json=log, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def load_test(duration_seconds=60, rps=100):
    print(f"Starting load test: {rps} requests/sec for {duration_seconds} seconds")
    
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        while time.time() - start_time < duration_seconds:
            batch_start = time.time()
            
            futures = [executor.submit(send_log) for _ in range(rps)]
            
            for future in futures:
                if future.result():
                    success_count += 1
                else:
                    error_count += 1
            
            # Sleep to maintain target RPS
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
    
    total = success_count + error_count
    print(f"\nLoad test complete:")
    print(f"  Total requests: {total}")
    print(f"  Successful: {success_count} ({success_count/total*100:.2f}%)")
    print(f"  Failed: {error_count} ({error_count/total*100:.2f}%)")

if __name__ == "__main__":
    load_test(duration_seconds=60, rps=100)
PYEOF

python3 /tmp/load-test.py
