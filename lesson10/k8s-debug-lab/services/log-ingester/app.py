"""
Log Ingester Service - Receives logs and publishes to Kafka
Intentionally resource-intensive for debugging exercises
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_RECEIVED = Counter('logs_received_total', 'Total logs received', ['source', 'level'])
PROCESSING_TIME = Histogram('log_processing_seconds', 'Time spent processing logs')
INGESTION_ERRORS = Counter('ingestion_errors_total', 'Total ingestion errors', ['error_type'])

app = FastAPI(
    title="Log Ingester Service",
    description="Receives and ingests logs for processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogEntry(BaseModel):
    """Schema for incoming log entries"""
    timestamp: Optional[datetime] = None
    level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    source: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=10000)
    metadata: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    kafka_connected: bool
    redis_connected: bool

# Simulated Kafka producer
class KafkaProducer:
    def __init__(self):
        self.connected = False
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        
    async def connect(self):
        """Simulate Kafka connection"""
        await asyncio.sleep(0.1)
        self.connected = True
        logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
        
    async def send(self, topic: str, value: dict):
        """Simulate sending message to Kafka"""
        if not self.connected:
            raise Exception("Kafka not connected")
        await asyncio.sleep(0.01)  # Simulate network latency
        logger.debug(f"Sent message to {topic}: {value}")

# Simulated Redis client
class RedisClient:
    def __init__(self):
        self.connected = False
        self.host = os.getenv('REDIS_HOST', 'redis')
        
    async def connect(self):
        """Simulate Redis connection"""
        await asyncio.sleep(0.05)
        self.connected = True
        logger.info(f"Connected to Redis at {self.host}")
        
    async def incr(self, key: str):
        """Simulate Redis increment"""
        if not self.connected:
            raise Exception("Redis not connected")
        await asyncio.sleep(0.001)

kafka_producer = KafkaProducer()
redis_client = RedisClient()

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("Starting Log Ingester Service...")
    try:
        await kafka_producer.connect()
        await redis_client.connect()
        logger.info("All connections established successfully")
    except Exception as e:
        logger.error(f"Failed to establish connections: {e}")
        # Don't raise - allow service to start for debugging

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        kafka_connected=kafka_producer.connected,
        redis_connected=redis_client.connected
    )

@app.get("/ready")
async def readiness_check():
    """Readiness check - are we ready to receive traffic?"""
    if not kafka_producer.connected:
        raise HTTPException(status_code=503, detail="Kafka not connected")
    if not redis_client.connected:
        raise HTTPException(status_code=503, detail="Redis not connected")
    return {"ready": True}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/ingest")
async def ingest_log(log_entry: LogEntry):
    """Ingest a single log entry"""
    start_time = time.time()
    
    try:
        # Set timestamp if not provided
        if log_entry.timestamp is None:
            log_entry.timestamp = datetime.utcnow()
        
        # Convert to dict for Kafka
        log_dict = log_entry.dict()
        log_dict['timestamp'] = log_dict['timestamp'].isoformat()
        
        # Send to Kafka
        await kafka_producer.send('logs', log_dict)
        
        # Update Redis counter
        await redis_client.incr(f"logs:{log_entry.source}:{log_entry.level}")
        
        # Update metrics
        LOGS_RECEIVED.labels(source=log_entry.source, level=log_entry.level).inc()
        PROCESSING_TIME.observe(time.time() - start_time)
        
        logger.info(f"Ingested log from {log_entry.source}: {log_entry.level}")
        
        return {
            "status": "accepted",
            "timestamp": log_entry.timestamp.isoformat(),
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
    except Exception as e:
        INGESTION_ERRORS.labels(error_type=type(e).__name__).inc()
        logger.error(f"Failed to ingest log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/batch")
async def ingest_batch(log_entries: list[LogEntry]):
    """Ingest multiple log entries"""
    results = []
    for entry in log_entries:
        try:
            result = await ingest_log(entry)
            results.append({"status": "success", "result": result})
        except HTTPException as e:
            results.append({"status": "error", "detail": e.detail})
    
    return {
        "total": len(log_entries),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "results": results
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
