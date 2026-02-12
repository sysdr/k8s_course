import json
import time
from kafka import KafkaConsumer
import redis
import structlog
from prometheus_client import Counter, Histogram, start_http_server

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Prometheus metrics
LOGS_PROCESSED = Counter('logs_processed_total', 'Total logs processed', ['level'])
PROCESSING_DURATION = Histogram('log_processing_duration_seconds', 'Processing duration')

class LogProcessor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'logs',
            bootstrap_servers='kafka:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='log-processor-group',
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        self.redis_client = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        
        logger.info("log_processor_initialized")
    
    def process_log(self, log_data):
        """Process a single log entry"""
        start_time = time.time()
        
        try:
            level = log_data.get('level', 'UNKNOWN')
            service = log_data.get('service', 'unknown')
            
            # Aggregate statistics
            self.redis_client.hincrby(f"service_stats:{service}", level, 1)
            self.redis_client.incr("total_logs_processed")
            
            # Store error logs separately for alerting
            if level in ['ERROR', 'FATAL']:
                self.redis_client.zadd(
                    "error_logs",
                    {json.dumps(log_data): time.time()}
                )
                # Keep only last 1000 error logs
                self.redis_client.zremrangebyrank("error_logs", 0, -1001)
            
            LOGS_PROCESSED.labels(level=level).inc()
            PROCESSING_DURATION.observe(time.time() - start_time)
            
            logger.info("log_processed", level=level, service=service)
            
        except Exception as e:
            logger.error("log_processing_failed", error=str(e))
    
    def run(self):
        """Start consuming and processing logs"""
        logger.info("starting_log_consumption")
        
        for message in self.consumer:
            try:
                self.process_log(message.value)
            except Exception as e:
                logger.error("message_processing_error", error=str(e))

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8001)
    
    # Start processing
    processor = LogProcessor()
    processor.run()
