"""
Locust load-test definition.
Install: pip install locust
Run:     locust -f tests/load_test_locust.py --host=http://localhost:8000 -w 50 -r 10
"""
import random
from locust import HttpUser, task, between

SEVERITIES = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
SERVICES   = ["auth-svc", "order-svc", "payment-svc", "notification-svc", "api-gateway"]


class IngestUser(HttpUser):
    wait_time = between(0.05, 0.2)   # 5–20 req/s per user

    @task(8)
    def ingest_event(self):
        payload = {
            "severity": random.choice(SEVERITIES),
            "service":  random.choice(SERVICES),
            "message":  f"locust event #{random.randint(1, 999999)}",
            "metadata": {"source": "locust", "run": "load-test"},
        }
        self.client.post("/ingest", json=payload)

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def metrics_check(self):
        self.client.get("/metrics")
