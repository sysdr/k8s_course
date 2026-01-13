import os
import json
import time
import logging
from datetime import datetime
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uvicorn

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
EVENTS_PRODUCED = Counter('events_produced_total', 'Total events produced', ['status'])
PRODUCE_DURATION = Histogram('produce_duration_seconds', 'Time spent producing messages')
BATCH_SIZE = Histogram('batch_size_messages', 'Number of messages per batch')

app = FastAPI(title="Kafka Producer Service")

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'logs-stream')

# Initialize Kafka producer with production settings
producer = None

def get_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
                compression_type='lz4',  # Compress batches
                linger_ms=100,  # Batch for 100ms
                batch_size=32768,  # 32KB batches
                buffer_memory=67108864,  # 64MB buffer
            )
            logger.info(f"Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise
    return producer

class LogEvent(BaseModel):
    service: str
    level: str
    message: str
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None

class BulkLogEvent(BaseModel):
    events: list[LogEvent]

@app.on_event("startup")
async def startup_event():
    """Initialize Kafka producer on startup"""
    get_producer()
    logger.info("Producer service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global producer
    if producer:
        producer.flush()
        producer.close()
    logger.info("Producer service shutdown")

@app.post("/produce")
async def produce_event(event: LogEvent):
    """Produce a single log event to Kafka"""
    try:
        with PRODUCE_DURATION.time():
            # Enrich event
            if not event.timestamp:
                event.timestamp = datetime.utcnow()
            
            event_dict = event.dict()
            event_dict['timestamp'] = event_dict['timestamp'].isoformat()
            
            # Send to Kafka
            kafka_producer = get_producer()
            future = kafka_producer.send(KAFKA_TOPIC, value=event_dict)
            
            # Wait for confirmation (synchronous for single events)
            record_metadata = future.get(timeout=10)
            
            EVENTS_PRODUCED.labels(status='success').inc()
            
            return {
                "status": "success",
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset
            }
    except KafkaError as e:
        EVENTS_PRODUCED.labels(status='error').inc()
        logger.error(f"Kafka error: {e}")
        raise HTTPException(status_code=500, detail=f"Kafka error: {str(e)}")
    except Exception as e:
        EVENTS_PRODUCED.labels(status='error').inc()
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/produce/bulk")
async def produce_bulk(bulk: BulkLogEvent):
    """Produce multiple log events in a batch"""
    try:
        with PRODUCE_DURATION.time():
            kafka_producer = get_producer()
            futures = []
            
            for event in bulk.events:
                if not event.timestamp:
                    event.timestamp = datetime.utcnow()
                
                event_dict = event.dict()
                event_dict['timestamp'] = event_dict['timestamp'].isoformat()
                
                future = kafka_producer.send(KAFKA_TOPIC, value=event_dict)
                futures.append(future)
            
            # Wait for all to complete
            for future in futures:
                future.get(timeout=10)
            
            EVENTS_PRODUCED.labels(status='success').inc(len(bulk.events))
            BATCH_SIZE.observe(len(bulk.events))
            
            return {
                "status": "success",
                "events_produced": len(bulk.events)
            }
    except Exception as e:
        EVENTS_PRODUCED.labels(status='error').inc()
        logger.error(f"Bulk produce error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Verify Kafka connection
        kafka_producer = get_producer()
        kafka_producer.bootstrap_connected()
        return {"status": "healthy", "kafka": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
