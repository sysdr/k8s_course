"""
Log Ingestion Service - Receives and processes log entries
Network Policy: Only accepts traffic from API Gateway
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
import json
import os
from prometheus_client import Counter, Histogram, generate_latest
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Log Ingestion Service",
    description="Processes incoming log entries",
    version="1.0.0"
)

# Prometheus metrics
INGESTION_COUNT = Counter(
    'log_ingestion_total',
    'Total logs ingested',
    ['level', 'service']
)
INGESTION_LATENCY = Histogram(
    'log_ingestion_duration_seconds',
    'Log ingestion latency'
)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.data-layer.svc.cluster.local:9092")
KAFKA_TOPIC = "logs"

# Initialize Kafka producer
producer = None

def get_kafka_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
    return producer

class LogEntry(BaseModel):
    level: str
    message: str
    service: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "log-ingestion"
    }

@app.get("/ready")
async def readiness_check():
    """Check Kafka connectivity"""
    try:
        kafka_producer = get_kafka_producer()
        if kafka_producer:
            return {"status": "ready", "kafka": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Kafka unavailable")
    
    raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(generate_latest(), media_type="text/plain")

@app.post("/ingest")
async def ingest_log(log_entry: LogEntry):
    """
    Ingest log entry and forward to Kafka
    Network Policy: Can only be called by api-gateway
    """
    start_time = time.time()
    
    try:
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
        if log_entry.level.upper() not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid log level. Must be one of: {valid_levels}"
            )
        
        # Add processing timestamp
        log_data = log_entry.dict()
        log_data['ingested_at'] = datetime.utcnow().isoformat()
        
        # Send to Kafka
        kafka_producer = get_kafka_producer()
        if kafka_producer:
            future = kafka_producer.send(KAFKA_TOPIC, value=log_data)
            try:
                record_metadata = future.get(timeout=10)
                logger.info(
                    f"Log sent to Kafka topic={record_metadata.topic} "
                    f"partition={record_metadata.partition} "
                    f"offset={record_metadata.offset}"
                )
            except KafkaError as e:
                logger.error(f"Kafka send failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to queue log")
        
        # Record metrics
        INGESTION_COUNT.labels(
            level=log_entry.level,
            service=log_entry.service
        ).inc()
        
        INGESTION_LATENCY.observe(time.time() - start_time)
        
        return {
            "status": "success",
            "message": "Log ingested successfully",
            "log_id": f"{log_entry.service}_{int(time.time() * 1000)}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
