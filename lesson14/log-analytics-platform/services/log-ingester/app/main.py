from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import asyncio
from kafka import KafkaProducer
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import logging
from pythonjsonlogger import jsonlogger

# Configure structured logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = FastAPI(title="Log Ingester Service", version="1.0.0")

# Prometheus metrics
log_ingestion_counter = Counter('logs_ingested_total', 'Total number of logs ingested', ['level', 'source'])
ingestion_duration = Histogram('log_ingestion_duration_seconds', 'Time spent ingesting logs')
kafka_publish_errors = Counter('kafka_publish_errors_total', 'Total Kafka publish errors')

# Kafka producer (initialized on startup)
kafka_producer = None

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level: DEBUG, INFO, WARN, ERROR, FATAL")
    message: str = Field(..., description="Log message")
    source: str = Field(..., description="Source system or application")
    host: Optional[str] = None
    metadata: Optional[dict] = {}

class BulkLogRequest(BaseModel):
    logs: List[LogEntry]

@app.on_event("startup")
async def startup_event():
    """Initialize Kafka producer on startup"""
    global kafka_producer
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=['kafka-0.kafka.log-analytics.svc.cluster.local:9092'],
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=5
        )
        logger.info("Kafka producer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close Kafka producer on shutdown"""
    if kafka_producer:
        kafka_producer.close()
        logger.info("Kafka producer closed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "log-ingester"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Verify Kafka connectivity
    if kafka_producer is None:
        raise HTTPException(status_code=503, detail="Kafka producer not initialized")
    return {"status": "ready", "kafka": "connected"}

@app.post("/ingest")
async def ingest_log(log: LogEntry, background_tasks: BackgroundTasks):
    """Ingest a single log entry"""
    start = datetime.utcnow()
    try:
        # Publish to Kafka
        log_dict = log.dict()
        kafka_producer.send('raw-logs', value=log_dict)
        kafka_producer.flush()  # Ensure message is sent immediately
        
        # Update metrics
        ingestion_time = (datetime.utcnow() - start).total_seconds()
        ingestion_duration.observe(ingestion_time)
        log_ingestion_counter.labels(level=log.level, source=log.source).inc()
        
        logger.info(f"Log ingested from {log.source}", extra={"level": log.level})
        
        return {"status": "accepted", "message": "Log entry queued for processing"}
    except Exception as e:
        kafka_publish_errors.inc()
        logger.error(f"Failed to ingest log: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/ingest/bulk")
async def ingest_bulk_logs(request: BulkLogRequest):
    """Ingest multiple log entries in bulk"""
    start = datetime.utcnow()
    try:
        success_count = 0
        for log in request.logs:
            try:
                log_dict = log.dict()
                kafka_producer.send('raw-logs', value=log_dict)
                log_ingestion_counter.labels(level=log.level, source=log.source).inc()
                success_count += 1
            except Exception as e:
                kafka_publish_errors.inc()
                logger.error(f"Failed to publish log to Kafka: {e}")
        
        # Flush to ensure all messages are sent
        kafka_producer.flush()
        
        ingestion_time = (datetime.utcnow() - start).total_seconds()
        ingestion_duration.observe(ingestion_time)
        
        logger.info(f"Bulk ingestion completed: {success_count}/{len(request.logs)} logs")
        
        return {
            "status": "accepted",
            "total": len(request.logs),
            "successful": success_count,
            "failed": len(request.logs) - success_count
        }
    except Exception as e:
        logger.error(f"Bulk ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk ingestion failed: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/stats")
async def get_stats():
    """Get ingestion statistics"""
    return {
        "service": "log-ingester",
        "version": "1.0.0",
        "kafka_connected": kafka_producer is not None
    }
