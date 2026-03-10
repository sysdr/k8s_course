"""
Load test for log ingestion service.
Usage: locust -f locustfile.py --host=http://localhost:8080 --users=100 --spawn-rate=10
"""
import random
import string
import uuid
from datetime import datetime
from locust import HttpUser, task, between, events


SERVICES = ["api-gateway", "auth-service", "payment-service", "order-service", "notification-service"]
LEVELS    = ["DEBUG", "INFO", "INFO", "INFO", "WARN", "ERROR"]


def random_message(length: int = 80) -> str:
    return "".join(random.choices(string.ascii_lowercase + " ", k=length))


class LogIngestionUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(8)
    def ingest_single(self):
        payload = {
            "event_id": str(uuid.uuid4()),
            "service": random.choice(SERVICES),
            "level": random.choice(LEVELS),
            "message": random_message(),
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": str(uuid.uuid4()),
            "span_id": str(uuid.uuid4())[:16],
            "metadata": {"pod": f"pod-{random.randint(1,10)}", "region": "us-east-1"}
        }
        self.client.post("/ingest", json=payload)

    @task(2)
    def ingest_batch(self):
        events_batch = [
            {
                "event_id": str(uuid.uuid4()),
                "service": random.choice(SERVICES),
                "level": random.choice(LEVELS),
                "message": random_message(60),
                "timestamp": datetime.utcnow().isoformat(),
            }
            for _ in range(random.randint(10, 50))
        ]
        self.client.post("/ingest/batch", json={"events": events_batch})


class LogQueryUser(HttpUser):
    wait_time = between(0.5, 2.0)
    host = "http://localhost:8081"

    @task(5)
    def query_logs(self):
        params = {"limit": 100}
        if random.random() > 0.5:
            params["level"] = random.choice(["ERROR", "WARN"])
        if random.random() > 0.7:
            params["service"] = random.choice(SERVICES)
        self.client.get("/logs", params=params)

    @task(1)
    def query_stats(self):
        params = {}
        if random.random() > 0.5:
            params["service"] = random.choice(SERVICES)
        self.client.get("/logs/stats", params=params)
