import os
import json
import time
import logging
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
EVENTS_CONSUMED = Counter('events_consumed_total', 'Total events consumed', ['status'])
PROCESSING_DURATION = Histogram('processing_duration_seconds', 'Event processing time')
CONSUMER_LAG = Gauge('consumer_lag_messages', 'Consumer lag in messages', ['partition'])
EVENTS_BY_LEVEL = Counter('events_by_level_total', 'Events by log level', ['level'])

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'logs-stream')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'log-processor')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# Initialize Redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class LogProcessor:
    def __init__(self):
        self.consumer = self.create_consumer()
        self.stats = defaultdict(int)
        
    def create_consumer(self):
        """Create Kafka consumer with production settings"""
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # Manual commit for exactly-once
                max_poll_records=500,  # Process in batches
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            logger.info(f"Consumer connected to {KAFKA_BOOTSTRAP_SERVERS}, group: {KAFKA_GROUP_ID}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create consumer: {e}")
            raise
    
    def process_event(self, event):
        """Process individual log event"""
        try:
            with PROCESSING_DURATION.time():
                # Extract fields
                service = event.get('service', 'unknown')
                level = event.get('level', 'INFO')
                message = event.get('message', '')
                timestamp = event.get('timestamp')
                
                # Update metrics
                EVENTS_BY_LEVEL.labels(level=level).inc()
                
                # Store in Redis for real-time dashboard
                # Use sorted set with timestamp as score
                redis_key = f"logs:{service}:{level}"
                redis_client.zadd(
                    redis_key,
                    {json.dumps(event): time.time()}
                )
                
                # Trim to last 1000 events per service/level
                redis_client.zremrangebyrank(redis_key, 0, -1001)
                
                # Update statistics
                stats_key = f"stats:{service}:{level}"
                redis_client.hincrby(stats_key, 'count', 1)
                redis_client.hset(stats_key, 'last_seen', timestamp or datetime.utcnow().isoformat())
                
                # Pattern detection for ERROR/CRITICAL
                if level in ['ERROR', 'CRITICAL']:
                    alert_key = f"alerts:{service}"
                    redis_client.lpush(alert_key, json.dumps(event))
                    redis_client.ltrim(alert_key, 0, 99)  # Keep last 100 alerts
                
                EVENTS_CONSUMED.labels(status='success').inc()
                self.stats['processed'] += 1
                
        except Exception as e:
            EVENTS_CONSUMED.labels(status='error').inc()
            logger.error(f"Error processing event: {e}")
            self.stats['errors'] += 1
    
    def update_lag_metrics(self):
        """Update consumer lag metrics"""
        try:
            # Get consumer lag per partition
            partitions = self.consumer.assignment()
            for partition in partitions:
                # Get current offset
                current_offset = self.consumer.position(partition)
                # Get high watermark (latest offset)
                high_watermark = self.consumer.highwater(partition)
                # Calculate lag
                lag = high_watermark - current_offset if high_watermark and current_offset else 0
                CONSUMER_LAG.labels(partition=str(partition.partition)).set(lag)
        except Exception as e:
            logger.error(f"Error updating lag metrics: {e}")
    
    def run(self):
        """Main consumer loop"""
        logger.info("Starting consumer loop...")
        
        try:
            while True:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000, max_records=500)
                
                if messages:
                    # Process batch
                    for topic_partition, records in messages.items():
                        for record in records:
                            self.process_event(record.value)
                    
                    # Commit offsets after successful processing
                    self.consumer.commit()
                    logger.info(f"Processed batch: {sum(len(r) for r in messages.values())} messages")
                
                # Update lag metrics every iteration
                self.update_lag_metrics()
                
                # Log stats every 100 batches
                if self.stats['processed'] % 10000 == 0 and self.stats['processed'] > 0:
                    logger.info(f"Stats - Processed: {self.stats['processed']}, Errors: {self.stats['errors']}")
                    
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.consumer.close()
            logger.info("Consumer closed")

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8001)
    logger.info("Metrics server started on port 8001")
    
    # Start processing
    processor = LogProcessor()
    processor.run()
