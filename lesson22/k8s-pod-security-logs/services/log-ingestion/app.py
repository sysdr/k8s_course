"""
Log Ingestion Service - Baseline Pod Security Policy
Handles high-throughput log ingestion from multiple tenants
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import asyncio
import redis.asyncio as aioredis
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Log Ingestion Service",
    description="High-performance log ingestion with baseline security",
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

# Configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Global Redis connection
redis_client = None

class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level: DEBUG, INFO, WARN, ERROR")
    service: str = Field(..., description="Service name")
    tenant: str = Field(..., description="Tenant identifier")
    message: str = Field(..., description="Log message")
    metadata: Optional[dict] = Field(default={}, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "level": "INFO",
                "service": "api-gateway",
                "tenant": "public",
                "message": "Request processed successfully",
                "metadata": {"request_id": "abc-123", "duration_ms": 45}
            }
        }

class LogBatch(BaseModel):
    """Batch log entries"""
    entries: List[LogEntry]
    
@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global redis_client
    try:
        redis_client = aioredis.from_url(
            f'redis://{REDIS_HOST}:{REDIS_PORT}',
            encoding='utf-8',
            decode_responses=True
        )
        await redis_client.ping()
        logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # Continue running even if Redis is unavailable
        redis_client = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        logger.info("Redis connection closed")

async def process_log(log: LogEntry):
    """Process individual log entry"""
    try:
        # Validate tenant
        valid_tenants = ["public", "payment", "system"]
        if log.tenant not in valid_tenants:
            raise ValueError(f"Invalid tenant: {log.tenant}")
        
        # Store in Redis for real-time access
        if redis_client:
            log_key = f"log:{log.tenant}:{log.timestamp.isoformat()}"
            await redis_client.setex(
                log_key,
                3600,  # 1 hour TTL
                json.dumps(log.model_dump(), default=str)
            )
        
        # TODO: Send to Kafka for persistent storage
        logger.info(f"Processed log from {log.service} (tenant: {log.tenant})")
        
    except Exception as e:
        logger.error(f"Error processing log: {e}")
        raise

@app.post("/ingest", status_code=202)
async def ingest_log(log: LogEntry, background_tasks: BackgroundTasks):
    """
    Ingest a single log entry
    
    Returns 202 Accepted to indicate async processing
    """
    try:
        background_tasks.add_task(process_log, log)
        return {
            "status": "accepted",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Log entry queued for processing"
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/batch", status_code=202)
async def ingest_batch(batch: LogBatch, background_tasks: BackgroundTasks):
    """
    Ingest multiple log entries in a batch
    
    More efficient for high-volume logging
    """
    try:
        for entry in batch.entries:
            background_tasks.add_task(process_log, entry)
        
        return {
            "status": "accepted",
            "count": len(batch.entries),
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"{len(batch.entries)} log entries queued"
        }
    except Exception as e:
        logger.error(f"Batch ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Kubernetes uses this for readiness and liveness probes
    """
    redis_status = "connected" if redis_client else "disconnected"
    return {
        "status": "healthy",
        "service": "log-ingestion",
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns basic metrics about log processing
    """
    # TODO: Implement proper Prometheus metrics
    return {
        "logs_processed_total": 0,
        "logs_failed_total": 0,
        "processing_duration_seconds": 0.0
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "log-ingestion",
        "version": "1.0.0",
        "security_policy": "baseline",
        "endpoints": {
            "ingest": "/ingest",
            "batch_ingest": "/ingest/batch",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
