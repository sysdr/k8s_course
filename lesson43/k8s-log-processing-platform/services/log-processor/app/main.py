"""
Log Processor Service - Stream processing with Kafka consumers
Processes, enriches, and aggregates log data in real-time
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any
import logging

from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import redis.asyncio as redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
logs_processed = Counter('logs_processed_total', 'Total logs processed', ['level'])
processing_duration = Histogram('log_processing_duration_seconds', 'Processing duration')
anomaly_detected = Counter('anomalies_detected_total', 'Anomalies detected')

app = FastAPI(title="Log Processor Service", version="1.0.0")

# Global state
kafka_consumer: AIOKafkaConsumer = None
kafka_producer: AIOKafkaProducer = None
redis_client: redis.Redis = None
processing_task = None

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
INPUT_TOPIC = os.getenv('INPUT_TOPIC', 'raw-logs')
OUTPUT_TOPIC = os.getenv('OUTPUT_TOPIC', 'processed-logs')

async def process_log_entry(log_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and enrich log entry
    - Add processing timestamp
    - Detect anomalies
    - Classify severity
    - Extract patterns
    """
    with processing_duration.time():
        processed = log_data.copy()
        processed['processed_at'] = datetime.utcnow().isoformat()
        
        # Anomaly detection: excessive error rate
        level = log_data.get('level', 'INFO')
        if level in ['ERROR', 'FATAL']:
            source = log_data.get('source', 'unknown')
            error_count = await redis_client.incr(f"errors:{source}")
            await redis_client.expire(f"errors:{source}", 300)  # 5 min window
            
            if error_count > 100:  # More than 100 errors in 5 minutes
                processed['anomaly'] = True
                processed['anomaly_type'] = 'high_error_rate'
                anomaly_detected.inc()
        
        # Pattern extraction from message
        message = log_data.get('message', '')
        if 'timeout' in message.lower():
            processed['tags'] = processed.get('tags', []) + ['timeout']
        if 'database' in message.lower():
            processed['tags'] = processed.get('tags', []) + ['database']
        
        logs_processed.labels(level=level).inc()
        
        return processed

async def consume_and_process():
    """Main processing loop - consumes from Kafka and processes logs"""
    logger.info("Starting log processing consumer...")
    
    while True:
        try:
            async for msg in kafka_consumer:
                log_data = json.loads(msg.value.decode('utf-8'))
                
                # Process the log
                processed_log = await process_log_entry(log_data)
                
                # Publish to processed topic
                await kafka_producer.send(
                    OUTPUT_TOPIC,
                    value=json.dumps(processed_log).encode('utf-8'),
                    key=msg.key
                )
                
                # Update metrics in Redis
                await update_metrics(processed_log)
                
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            await asyncio.sleep(1)

async def update_metrics(log_data: Dict[str, Any]):
    """Update aggregated metrics in Redis"""
    source = log_data.get('source', 'unknown')
    level = log_data.get('level', 'INFO')
    
    # Increment counters
    await redis_client.hincrby(f"metrics:{source}", level, 1)
    await redis_client.expire(f"metrics:{source}", 3600)  # 1 hour TTL

@app.on_event("startup")
async def startup_event():
    """Initialize Kafka consumers/producers and start processing"""
    global kafka_consumer, kafka_producer, redis_client, processing_task
    
    # Initialize Kafka consumer
    kafka_consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id='log-processor-group',
        value_deserializer=lambda m: m.decode('utf-8'),
        enable_auto_commit=True,
        auto_offset_reset='latest'
    )
    await kafka_consumer.start()
    logger.info(f"Kafka consumer started for topic: {INPUT_TOPIC}")
    
    # Initialize Kafka producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        compression_type='gzip'
    )
    await kafka_producer.start()
    logger.info(f"Kafka producer started for topic: {OUTPUT_TOPIC}")
    
    # Initialize Redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )
    await redis_client.ping()
    logger.info("Redis connected")
    
    # Start background processing
    processing_task = asyncio.create_task(consume_and_process())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if processing_task:
        processing_task.cancel()
    if kafka_consumer:
        await kafka_consumer.stop()
    if kafka_producer:
        await kafka_producer.stop()
    if redis_client:
        await redis_client.close()

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
