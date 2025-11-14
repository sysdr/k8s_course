"""
Log Ingestion API - FastAPI Service
Accepts log events, validates them, and publishes to Redis streams.
Demonstrates: health probes, graceful shutdown, metrics endpoints.
"""
import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Metrics
log_ingestion_counter = Counter('log_ingestion_total', 'Total log events ingested', ['level'])
log_ingestion_duration = Histogram('log_ingestion_duration_seconds', 'Log ingestion duration')
redis_connection_errors = Counter('redis_connection_errors_total', 'Redis connection errors')

# Global state
redis_client: Optional[redis.Redis] = None
shutdown_event = asyncio.Event()

class LogEvent(BaseModel):
    """Log event data model"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    service: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=10000)
    metadata: dict = Field(default_factory=dict)
    
    @validator('level')
    def validate_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Level must be one of {allowed_levels}')
        return v.upper()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global redis_client
    
    # Startup
    redis_client = await redis.from_url(
        "redis://redis-service:6379",
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        health_check_interval=30
    )
    log_info("Connected to Redis")
    
    yield
    
    # Shutdown
    log_info("Shutting down gracefully...")
    shutdown_event.set()
    if redis_client:
        await redis_client.close()
    log_info("Shutdown complete")

app = FastAPI(
    title="Log Ingestion API",
    description="High-performance log ingestion service with Redis stream processing",
    version="1.0.0",
    lifespan=lifespan
)

def log_info(msg: str):
    """Structured logging"""
    print(f"[INFO] {datetime.utcnow().isoformat()} - {msg}", flush=True)

@app.get("/healthz", status_code=200)
async def liveness_probe():
    """
    Liveness probe - checks if the application is running.
    Kubernetes will restart the pod if this fails.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready", status_code=200)
async def readiness_probe():
    """
    Readiness probe - checks if the application can handle traffic.
    Kubernetes removes pod from service endpoints if this fails.
    """
    try:
        if redis_client:
            await redis_client.ping()
            return {
                "status": "ready",
                "redis": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis client not initialized"
            )
    except Exception as e:
        redis_connection_errors.inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {str(e)}"
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/ingest", status_code=202)
@log_ingestion_duration.time()
async def ingest_log(log_event: LogEvent):
    """
    Ingest a log event and publish to Redis stream.
    Returns 202 Accepted immediately - processing is asynchronous.
    """
    try:
        if not redis_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable"
            )
        
        # Publish to Redis stream
        stream_key = "logs:stream"
        message_data = {
            "timestamp": log_event.timestamp.isoformat(),
            "level": log_event.level,
            "service": log_event.service,
            "message": log_event.message,
            "metadata": str(log_event.metadata)
        }
        
        message_id = await redis_client.xadd(stream_key, message_data)
        
        # Update metrics
        log_ingestion_counter.labels(level=log_event.level).inc()
        
        return {
            "status": "accepted",
            "message_id": message_id,
            "stream": stream_key
        }
        
    except Exception as e:
        log_info(f"Ingestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process log event"
        )

@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "Log Ingestion API",
        "version": "1.0.0",
        "endpoints": {
            "ingest": "/api/v1/ingest",
            "health": "/healthz",
            "readiness": "/ready",
            "metrics": "/metrics"
        }
    }

def handle_shutdown(signum, frame):
    """Graceful shutdown signal handler"""
    log_info(f"Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
