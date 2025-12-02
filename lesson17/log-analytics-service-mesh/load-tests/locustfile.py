from locust import HttpUser, task, between
import random
import json

class LogIngestionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def ingest_single_log(self):
        severities = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
        services = ['api-service', 'auth-service', 'data-service', 'notification-service']
        
        payload = {
            'tenant_id': f'tenant-{random.randint(1, 10)}',
            'service': random.choice(services),
            'severity': random.choice(severities),
            'message': f'Test log message {random.randint(1, 10000)}',
            'metadata': {
                'request_id': f'req-{random.randint(10000, 99999)}',
                'user_id': f'user-{random.randint(1, 1000)}'
            }
        }
        
        self.client.post('/api/v1/ingest', json=payload)
    
    @task(1)
    def query_logs(self):
        tenant_id = f'tenant-{random.randint(1, 10)}'
        self.client.get(f'/api/v1/logs?tenant_id={tenant_id}&limit=50')
    
    @task(1)
    def get_statistics(self):
        tenant_id = f'tenant-{random.randint(1, 10)}'
        self.client.get(f'/api/v1/statistics?tenant_id={tenant_id}&hours=24')
