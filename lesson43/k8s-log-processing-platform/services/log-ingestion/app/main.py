"""
Log Ingestion Service - Production-grade log collection API
Handles 10K+ logs/second with async processing and Kafka integration
"""
import asyncio
import json
import time
from datetime import datetime
from typing import List, Optional
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
log_ingestion_counter = Counter('log_ingestion_total', 'Total logs ingested', ['level', 'source'])
log_processing_duration = Histogram('log_processing_seconds', 'Log processing duration')
kafka_publish_errors = Counter('kafka_publish_errors_total', 'Kafka publish failures')

# Pydantic models
class LogEntry(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level: INFO, WARN, ERROR, FATAL")
    message: str = Field(..., min_length=1, max_length=10000)
    source: str = Field(..., description="Service or application name")
    trace_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[dict] = Field(default_factory=dict)
    
    @validator('level')
    def validate_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
        if v.upper() not in allowed:
            raise ValueError(f'Level must be one of {allowed}')
        return v.upper()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    dependencies: dict

# FastAPI app initialization
app = FastAPI(
    title="Log Ingestion Service",
    description="High-throughput log collection API with Kafka backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connections
kafka_producer: Optional[AIOKafkaProducer] = None
redis_client: Optional[redis.Redis] = None

# Configuration from environment
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'raw-logs')

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global kafka_producer, redis_client
    
    # Initialize Kafka producer with retry logic
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        compression_type='gzip',
        linger_ms=10,  # Batch messages for 10ms for efficiency
        request_timeout_ms=30000,
        retry_backoff_ms=100
    )
    await kafka_producer.start()
    logger.info(f"Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}")
    
    # Initialize Redis for caching and rate limiting
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5
    )
    await redis_client.ping()
    logger.info(f"Redis connected to {REDIS_HOST}:{REDIS_PORT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown"""
    if kafka_producer:
        await kafka_producer.stop()
    if redis_client:
        await redis_client.close()
    logger.info("Connections closed gracefully")

@app.post("/api/v1/logs", status_code=202)
async def ingest_log(log_entry: LogEntry, background_tasks: BackgroundTasks):
    """
    Ingest a single log entry
    Returns 202 Accepted for async processing
    """
    with log_processing_duration.time():
        try:
            # Increment metrics
            log_ingestion_counter.labels(
                level=log_entry.level,
                source=log_entry.source
            ).inc()
            
            # Add to processing queue
            background_tasks.add_task(publish_to_kafka, log_entry)
            
            # Cache recent logs in Redis for quick access
            cache_key = f"recent:{log_entry.source}:{int(time.time())}"
            await redis_client.setex(
                cache_key,
                300,  # 5 minute TTL
                json.dumps(log_entry.dict(), default=str)
            )
            # Update dashboard metrics in Redis (same format as log-processor)
            await redis_client.hincrby(f"metrics:{log_entry.source}", log_entry.level, 1)
            await redis_client.expire(f"metrics:{log_entry.source}", 3600)

            return {
                "status": "accepted",
                "trace_id": log_entry.trace_id,
                "timestamp": log_entry.timestamp
            }
            
        except Exception as e:
            logger.error(f"Log ingestion failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal processing error")

@app.post("/api/v1/logs/batch", status_code=202)
async def ingest_logs_batch(logs: List[LogEntry], background_tasks: BackgroundTasks):
    """
    Batch ingest multiple log entries
    Optimized for high-throughput scenarios
    """
    if len(logs) > 1000:
        raise HTTPException(status_code=400, detail="Batch size exceeds limit of 1000")
    
    try:
        for log_entry in logs:
            log_ingestion_counter.labels(
                level=log_entry.level,
                source=log_entry.source
            ).inc()
        
        # Async batch publishing
        background_tasks.add_task(publish_batch_to_kafka, logs)
        
        return {
            "status": "accepted",
            "count": len(logs),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Batch ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch processing error")

async def publish_to_kafka(log_entry: LogEntry):
    """Publish log entry to Kafka topic"""
    try:
        await kafka_producer.send_and_wait(
            KAFKA_TOPIC,
            value=log_entry.dict(by_alias=True),
            key=log_entry.source.encode('utf-8')
        )
    except Exception as e:
        kafka_publish_errors.inc()
        logger.error(f"Kafka publish failed: {str(e)}")

async def publish_batch_to_kafka(logs: List[LogEntry]):
    """Publish batch of logs to Kafka efficiently"""
    try:
        tasks = []
        for log_entry in logs:
            task = kafka_producer.send(
                KAFKA_TOPIC,
                value=log_entry.dict(by_alias=True),
                key=log_entry.source.encode('utf-8')
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        kafka_publish_errors.inc()
        logger.error(f"Batch Kafka publish failed: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Validates all dependencies
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "dependencies": {}
    }
    
    # Check Kafka
    try:
        if kafka_producer and kafka_producer._sender:
            health_status["dependencies"]["kafka"] = "connected"
        else:
            health_status["dependencies"]["kafka"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["dependencies"]["kafka"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        await redis_client.ping()
        health_status["dependencies"]["redis"] = "connected"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return Response(
        content=json.dumps(health_status, default=str),
        status_code=status_code,
        media_type="application/json"
    )

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        await redis_client.ping()
        return {"status": "ready"}
    except:
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
