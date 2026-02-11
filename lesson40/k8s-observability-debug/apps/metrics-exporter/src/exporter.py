"""
Custom Metrics Exporter
Generates synthetic metrics for testing observability stack
"""
import time
import random
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom business metrics
database_connections = Gauge(
    'database_connections_active',
    'Number of active database connections',
    ['database', 'pool']
)

cache_hit_rate = Gauge(
    'cache_hit_rate_percent',
    'Cache hit rate percentage',
    ['cache_type']
)

batch_processing_duration = Histogram(
    'batch_processing_duration_seconds',
    'Time taken to process log batches',
    ['batch_size_category'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

queue_depth = Gauge(
    'message_queue_depth',
    'Number of messages in processing queue',
    ['queue_name', 'priority']
)

def generate_metrics():
    """Generate synthetic metrics data"""
    while True:
        try:
            # Database connections
            for db in ['primary', 'replica', 'analytics']:
                for pool in ['read', 'write']:
                    database_connections.labels(
                        database=db,
                        pool=pool
                    ).set(random.randint(10, 100))
            
            # Cache metrics
            for cache_type in ['redis', 'memcached', 'local']:
                cache_hit_rate.labels(
                    cache_type=cache_type
                ).set(random.uniform(70.0, 99.5))
            
            # Batch processing
            for category in ['small', 'medium', 'large']:
                duration = random.uniform(0.5, 15.0)
                batch_processing_duration.labels(
                    batch_size_category=category
                ).observe(duration)
            
            # Queue depth
            for queue in ['ingestion', 'processing', 'export']:
                for priority in ['high', 'normal', 'low']:
                    queue_depth.labels(
                        queue_name=queue,
                        priority=priority
                    ).set(random.randint(0, 1000))
            
            logger.info("Metrics generated successfully")
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            time.sleep(5)

if __name__ == '__main__':
    logger.info("Starting metrics exporter on port 8081")
    start_http_server(8081)
    generate_metrics()
