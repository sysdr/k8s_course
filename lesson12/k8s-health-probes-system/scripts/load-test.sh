#!/bin/bash
set -euo pipefail

echo "Running load test..."

# Install locust if not present
if ! command -v locust &> /dev/null; then
    pip install locust --break-system-packages
fi

# Create locustfile
cat > /tmp/locustfile.py << 'LOCUST'
from locust import HttpUser, task, between
import json

class LogUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task(3)
    def send_log(self):
        self.client.post("/collector/logs", json={
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "INFO",
            "service": "test-service",
            "message": "Test log message"
        })
    
    @task(1)
    def get_summary(self):
        self.client.get("/api/api/logs/summary")
    
    @task(1)
    def get_recent(self):
        self.client.get("/api/api/logs/recent?limit=10")
LOCUST

# Get frontend URL
FRONTEND_URL=$(kubectl get svc frontend -n log-analytics -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
if [ "$FRONTEND_URL" == "" ] || [ "$FRONTEND_URL" == "localhost" ]; then
    kubectl port-forward svc/frontend 8080:80 -n log-analytics &
    FRONTEND_URL="http://localhost:8080"
    sleep 3
fi

echo "Starting load test against $FRONTEND_URL"
locust -f /tmp/locustfile.py --host=$FRONTEND_URL --users 50 --spawn-rate 10 --run-time 2m --headless
