import random
import time
from locust import HttpUser, task, between

class LogGeneratorUser(HttpUser):
    wait_time = between(0.1, 1)
    
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
    SERVICES = ['api-gateway', 'auth-service', 'payment-service', 'user-service', 'notification-service']
    
    MESSAGES = [
        "Request processed successfully",
        "Database connection established",
        "Cache hit for key",
        "Authentication token validated",
        "Rate limit exceeded",
        "Request validation failed",
        "Downstream service timeout",
        "Circuit breaker opened",
        "Memory usage high",
        "Disk space low"
    ]
    
    @task(70)
    def send_info_log(self):
        """Send INFO level log (most common)"""
        self.send_log('INFO')
    
    @task(20)
    def send_debug_log(self):
        """Send DEBUG level log"""
        self.send_log('DEBUG')
    
    @task(7)
    def send_warn_log(self):
        """Send WARN level log"""
        self.send_log('WARN')
    
    @task(2)
    def send_error_log(self):
        """Send ERROR level log"""
        self.send_log('ERROR')
    
    @task(1)
    def send_fatal_log(self):
        """Send FATAL level log"""
        self.send_log('FATAL')
    
    def send_log(self, level):
        payload = {
            "level": level,
            "message": random.choice(self.MESSAGES),
            "service": random.choice(self.SERVICES),
            "timestamp": time.time(),
            "metadata": {
                "request_id": f"req_{random.randint(10000, 99999)}",
                "user_id": f"user_{random.randint(1, 1000)}",
                "endpoint": f"/api/v1/{random.choice(['users', 'orders', 'products'])}"
            }
        }
        
        with self.client.post("/api/v1/logs", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
