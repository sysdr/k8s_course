from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import redis.asyncio as redis
import json
import logging
import asyncio
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Ingest API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client: Optional[redis.Redis] = None

class LogEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    service: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=10000)
    metadata: dict = Field(default_factory=dict)

class LogBatch(BaseModel):
    logs: List[LogEntry]

# Metrics
metrics = {
    "logs_received": 0,
    "logs_queued": 0,
    "errors": 0
}

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    
    try:
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        await redis_client.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "log-ingest"}

@app.get("/ready")
async def ready():
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Redis not connected")
    try:
        await redis_client.ping()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unreachable")

@app.get("/metrics")
async def get_metrics():
    return metrics

@app.post("/logs")
async def ingest_log(log_entry: LogEntry, background_tasks: BackgroundTasks):
    """Ingest a single log entry"""
    metrics["logs_received"] += 1
    
    if redis_client is None:
        metrics["errors"] += 1
        raise HTTPException(status_code=503, detail="Queue unavailable")
    
    try:
        # Queue log for processing
        log_data = log_entry.dict()
        await redis_client.rpush("log_queue", json.dumps(log_data))
        metrics["logs_queued"] += 1
        
        return {
            "status": "queued",
            "log_id": log_data["timestamp"]
        }
    except Exception as e:
        metrics["errors"] += 1
        logger.error(f"Failed to queue log: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue log")

@app.post("/logs/batch")
async def ingest_batch(batch: LogBatch):
    """Ingest multiple log entries in batch"""
    metrics["logs_received"] += len(batch.logs)
    
    if redis_client is None:
        metrics["errors"] += 1
        raise HTTPException(status_code=503, detail="Queue unavailable")
    
    try:
        # Use pipeline for efficient batch insertion
        async with redis_client.pipeline(transaction=True) as pipe:
            for log_entry in batch.logs:
                log_data = log_entry.dict()
                pipe.rpush("log_queue", json.dumps(log_data))
            await pipe.execute()
        
        metrics["logs_queued"] += len(batch.logs)
        
        return {
            "status": "queued",
            "count": len(batch.logs)
        }
    except Exception as e:
        metrics["errors"] += 1
        logger.error(f"Failed to queue batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue logs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
