from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import logging
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import redis.asyncio as redis
import os

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Log Analytics API",
    description="Production-grade log ingestion and query API",
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

# Prometheus metrics
log_counter = Counter('logs_ingested_total', 'Total logs ingested')
query_duration = Histogram('query_duration_seconds', 'Query duration')

# Models
class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    service: str
    message: str
    metadata: Optional[dict] = {}

class LogQuery(BaseModel):
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)

# Redis connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_host = os.getenv("REDIS_HOST", "redis-service")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    
    try:
        redis_client = await redis.from_url(
            f"redis://{redis_host}:{redis_port}",
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-service"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness probe - checks dependencies"""
    try:
        if redis_client:
            await redis_client.ping()
        return {"status": "ready", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")

@app.post("/logs", status_code=201)
async def ingest_log(log: LogEntry):
    """Ingest a log entry"""
    try:
        # Store in Redis with TTL
        log_key = f"log:{log.service}:{log.timestamp.timestamp()}"
        if redis_client:
            await redis_client.setex(
                log_key,
                3600,  # 1 hour TTL
                log.model_dump_json()
            )
        
        log_counter.inc()
        logger.info(f"Log ingested: {log.service} - {log.level}")
        
        return {"status": "success", "log_id": log_key}
    except Exception as e:
        logger.error(f"Failed to ingest log: {e}")
        raise HTTPException(status_code=500, detail="Ingestion failed")

@app.post("/logs/query")
async def query_logs(query: LogQuery):
    """Query logs with filters"""
    with query_duration.time():
        try:
            # Simulated query - in production, use proper database
            logs = []
            
            if redis_client:
                pattern = f"log:{query.service or '*'}:*"
                keys = []
                async for key in redis_client.scan_iter(match=pattern):
                    keys.append(key)
                    if len(keys) >= query.limit:
                        break
                
                for key in keys:
                    log_data = await redis_client.get(key)
                    if log_data:
                        logs.append(log_data)
            
            return {
                "total": len(logs),
                "logs": logs,
                "query": query.model_dump()
            }
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise HTTPException(status_code=500, detail="Query failed")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        total_keys = 0
        if redis_client:
            total_keys = await redis_client.dbsize()
        
        return {
            "total_logs": total_keys,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": str(e)}
