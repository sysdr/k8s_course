"""
Log Ingest Service - Cost-Optimized FastAPI Application
Demonstrates resource-efficient async patterns for Kubernetes FinOps
"""
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import uvicorn
import redis.asyncio as redis
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Log Ingest Service",
    description="Cost-optimized log ingestion with FinOps metrics",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
LOGS_INGESTED = Counter(
    'logs_ingested_total',
    'Total logs ingested',
    ['source', 'severity']
)

INGESTION_LATENCY = Histogram(
    'log_ingestion_duration_seconds',
    'Log ingestion latency',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

COST_PER_LOG = Gauge(
    'cost_per_log_cents',
    'Estimated cost per log ingested in cents'
)

MEMORY_USAGE = Gauge(
    'process_memory_bytes',
    'Process memory usage'
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

# Redis client (lazy initialization)
redis_client = None

class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: str
    source: str
    severity: str
    message: str
    metadata: Dict[str, Any] = {}

class LogBatch(BaseModel):
    """Batch of log entries"""
    logs: List[LogEntry]

async def get_redis():
    """Get Redis client with connection pooling"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )
    return redis_client

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting log ingest service...")
    try:
        await get_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Running in degraded mode.")
    
    # Initialize cost metrics
    COST_PER_LOG.set(0.00012)  # $0.00012 per log

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "log-ingest"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        if redis_client:
            await redis_client.ping()
        return {"status": "ready", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")

@app.post("/ingest")
async def ingest_log(log: LogEntry, background_tasks: BackgroundTasks):
    """Ingest single log entry"""
    start_time = time.time()
    
    try:
        # Record metrics
        LOGS_INGESTED.labels(source=log.source, severity=log.severity).inc()
        ACTIVE_CONNECTIONS.inc()
        
        # Process log asynchronously
        background_tasks.add_task(process_log, log.dict())
        
        # Record latency
        duration = time.time() - start_time
        INGESTION_LATENCY.observe(duration)
        
        return {
            "status": "accepted",
            "log_id": f"{log.source}-{int(time.time() * 1000)}",
            "processing_time_ms": round(duration * 1000, 2)
        }
    finally:
        ACTIVE_CONNECTIONS.dec()

@app.post("/ingest/batch")
async def ingest_batch(batch: LogBatch, background_tasks: BackgroundTasks):
    """Ingest batch of logs (cost-optimized)"""
    start_time = time.time()
    
    try:
        ACTIVE_CONNECTIONS.inc()
        
        # Process batch asynchronously
        for log in batch.logs:
            LOGS_INGESTED.labels(source=log.source, severity=log.severity).inc()
            background_tasks.add_task(process_log, log.dict())
        
        duration = time.time() - start_time
        INGESTION_LATENCY.observe(duration)
        
        return {
            "status": "accepted",
            "count": len(batch.logs),
            "processing_time_ms": round(duration * 1000, 2),
            "avg_time_per_log_ms": round(duration * 1000 / len(batch.logs), 2)
        }
    finally:
        ACTIVE_CONNECTIONS.dec()

async def process_log(log_data: Dict[str, Any]):
    """Background log processing"""
    try:
        client = await get_redis()
        
        # Store in Redis with TTL (cost optimization: expire old logs)
        log_key = f"log:{log_data['source']}:{int(time.time() * 1000)}"
        await client.setex(
            log_key,
            3600,  # 1 hour TTL
            json.dumps(log_data)
        )
        
        # Update processing statistics
        await client.hincrby("stats:logs", log_data['source'], 1)
        
    except Exception as e:
        logger.error(f"Error processing log: {e}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/stats")
async def get_stats():
    """Get ingestion statistics"""
    try:
        client = await get_redis()
        stats = await client.hgetall("stats:logs")
        
        return {
            "total_logs": sum(int(v) for v in stats.values()),
            "by_source": {k: int(v) for k, v in stats.items()},
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Optimize for cost/performance
        log_level="info"
    )
