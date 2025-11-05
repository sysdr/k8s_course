from locust import HttpUser, task, between
import json
import random
from datetime import datetime

class LogPlatformUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    services = ['auth-service', 'api-gateway', 'payment-service', 'user-service', 'notification-service']
    
    @task(10)
    def submit_single_log(self):
        log_data = {
            "level": random.choice(self.log_levels),
            "message": f"Test log message {random.randint(1, 10000)}",
            "service": random.choice(self.services),
            "metadata": {
                "request_id": f"req-{random.randint(1, 100000)}",
                "user_id": f"user-{random.randint(1, 10000)}"
            }
        }
        
        self.client.post(
            "/api/v1/logs",
            json=log_data,
            headers={"Content-Type": "application/json"}
        )
    
    @task(3)
    def submit_batch_logs(self):
        batch_size = random.randint(10, 100)
        logs = []
        
        for _ in range(batch_size):
            logs.append({
                "level": random.choice(self.log_levels),
                "message": f"Batch log message {random.randint(1, 10000)}",
                "service": random.choice(self.services),
                "metadata": {
                    "batch_id": f"batch-{random.randint(1, 1000)}"
                }
            })
        
        self.client.post(
            "/api/v1/logs/batch",
            json=logs,
            headers={"Content-Type": "application/json"}
        )
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
