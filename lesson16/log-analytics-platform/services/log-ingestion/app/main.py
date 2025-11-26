from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict
import asyncio
import json
import os
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Ingestion Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
logs_ingested = Counter('logs_ingested_total', 'Total logs ingested', ['level', 'source'])
ingestion_latency = Histogram('log_ingestion_latency_seconds', 'Log ingestion latency')

# In-memory storage (in production, use Redis/Kafka/Database)
log_store = []

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    message: str
    source: str
    metadata: Optional[Dict] = None

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "log-ingestion",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def ready():
    # In production, check database connections, kafka, etc.
    return {"status": "ready"}

@app.post("/api/ingest")
@ingestion_latency.time()
async def ingest_logs(log_entry: LogEntry):
    try:
        log_data = log_entry.dict()
        log_data['timestamp'] = log_data['timestamp'].isoformat()
        
        # Store log (in production, send to Kafka/write to database)
        log_store.append(log_data)
        
        # Update metrics
        logs_ingested.labels(
            level=log_entry.level,
            source=log_entry.source
        ).inc()
        
        logger.info(f"Ingested log: {log_entry.level} from {log_entry.source}")
        
        # Keep only last 10000 logs in memory
        if len(log_store) > 10000:
            log_store.pop(0)
        
        return {
            "status": "success",
            "log_id": len(log_store) - 1,
            "message": "Log ingested successfully"
        }
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/ingest/batch")
async def ingest_batch(logs: list[LogEntry]):
    ingested_count = 0
    for log_entry in logs:
        log_data = log_entry.dict()
        log_data['timestamp'] = log_data['timestamp'].isoformat()
        log_store.append(log_data)
        logs_ingested.labels(level=log_entry.level, source=log_entry.source).inc()
        ingested_count += 1
    
    return {
        "status": "success",
        "ingested": ingested_count,
        "total_logs": len(log_store)
    }

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/stats")
async def get_stats():
    return {
        "total_logs": len(log_store),
        "service": "log-ingestion",
        "uptime_seconds": os.getenv("UPTIME", "0")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
