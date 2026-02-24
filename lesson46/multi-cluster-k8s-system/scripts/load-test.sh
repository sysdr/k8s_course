#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Running load test across clusters..."

cat > /tmp/locustfile.py << 'LOCUST_EOF'
from locust import HttpUser, task, between
import random
import json
from datetime import datetime

class LogUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def send_logs(self):
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": random.choice(["INFO", "WARNING", "ERROR"]),
                "service": random.choice(["api", "worker", "scheduler"]),
                "message": f"Test log message {random.randint(1, 1000)}",
                "metadata": {"test": True}
            }
            for _ in range(10)
        ]
        
        self.client.post("/api/v1/logs", json=logs)
LOCUST_EOF

pip install locust

locust -f /tmp/locustfile.py --host=http://localhost:30080 --users 100 --spawn-rate 10 --run-time 5m

echo "Load test complete!"
