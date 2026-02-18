from locust import HttpUser, task, between
import random

class LogPlatformUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task(10)
    def ingest_single_log(self):
        """Send single log entry"""
        log_levels = ["DEBUG", "INFO", "WARN", "ERROR"]
        sources = ["webapp", "api", "database", "cache", "queue"]
        
        payload = {
            "level": random.choice(log_levels),
            "message": f"Test log message {random.randint(1, 10000)}",
            "source": random.choice(sources),
            "metadata": {
                "request_id": f"req_{random.randint(1, 1000000)}",
                "user_id": f"user_{random.randint(1, 10000)}"
            }
        }
        
        self.client.post("/api/v1/logs", json=payload)
    
    @task(2)
    def ingest_batch(self):
        """Send batch of logs"""
        batch_size = random.randint(10, 50)
        log_levels = ["DEBUG", "INFO", "WARN", "ERROR"]
        sources = ["webapp", "api", "database"]
        
        batch = []
        for i in range(batch_size):
            batch.append({
                "level": random.choice(log_levels),
                "message": f"Batch log {i}",
                "source": random.choice(sources)
            })
        
        self.client.post("/api/v1/logs/batch", json=batch)
    
    @task(1)
    def get_analytics(self):
        """Query analytics API"""
        self.client.get("/api/v1/analytics/summary")
