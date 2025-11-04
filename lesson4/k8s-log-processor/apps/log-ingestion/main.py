from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import time
import redis
import os
from datetime import datetime

app = FastAPI(title="Log Ingestion Service")
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis-service"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    source: str
    metadata: Optional[dict] = None

@app.post("/ingest")
async def ingest_log(log: LogEntry):
    """Ingest a log entry and store in Redis"""
    try:
        log_dict = log.dict()
        log_dict["processed_at"] = datetime.utcnow().isoformat()
        redis_client.lpush("logs", json.dumps(log_dict))
        redis_client.incr("log_count")
        return {"status": "success", "message": "Log ingested"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "log-ingestion"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        count = redis_client.get("log_count") or "0"
        return {
            "log_count": int(count),
            "service": "log-ingestion"
        }
    except:
        return {"log_count": 0, "service": "log-ingestion"}
