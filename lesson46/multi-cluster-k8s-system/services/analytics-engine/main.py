from fastapi import FastAPI, Query
from kafka import KafkaConsumer
import json
import logging
import threading
from collections import defaultdict
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Engine", version="1.0.0")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CLUSTER_NAME = os.getenv("CLUSTER_NAME", "unknown")

class AnalyticsEngine:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'processed-logs',
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=f'analytics-{CLUSTER_NAME}',
            auto_offset_reset='earliest'
        )
        
        self.metrics = defaultdict(lambda: defaultdict(int))
        self.error_patterns = []
        
    def analyze_logs(self):
        """Analyze processed logs"""
        for message in self.consumer:
            try:
                log_data = message.value
                
                # Update metrics
                service = log_data.get('service', 'unknown')
                level = log_data.get('level', 'unknown')
                
                self.metrics[service][level] += 1
                self.metrics[service]['total'] += 1
                
                # Track errors
                if level in ['ERROR', 'CRITICAL']:
                    self.error_patterns.append({
                        'timestamp': log_data['timestamp'],
                        'service': service,
                        'message': log_data['message'],
                        'cluster': log_data.get('cluster', 'unknown')
                    })
                    
                    # Keep only last 1000 errors
                    if len(self.error_patterns) > 1000:
                        self.error_patterns = self.error_patterns[-1000:]
                        
            except Exception as e:
                logger.error(f"Analytics error: {str(e)}")

analytics = AnalyticsEngine()

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting analytics engine in cluster: {CLUSTER_NAME}")
    analytics_thread = threading.Thread(target=analytics.analyze_logs, daemon=True)
    analytics_thread.start()

@app.get("/api/v1/analytics/metrics")
async def get_metrics(service: str = Query(None)):
    """Get aggregated metrics"""
    if service:
        return {
            "service": service,
            "metrics": dict(analytics.metrics.get(service, {})),
            "cluster": CLUSTER_NAME
        }
    
    return {
        "all_services": {k: dict(v) for k, v in analytics.metrics.items()},
        "cluster": CLUSTER_NAME
    }

@app.get("/api/v1/analytics/errors")
async def get_errors(limit: int = Query(100, le=1000)):
    """Get recent errors"""
    return {
        "errors": analytics.error_patterns[-limit:],
        "total_errors": len(analytics.error_patterns),
        "cluster": CLUSTER_NAME
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "cluster": CLUSTER_NAME,
        "services_tracked": len(analytics.metrics)
    }
