"""
Analytics API Service - Query and aggregate processed log data
Provides REST API for frontend dashboard
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional
import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis
from prometheus_client import generate_latest
from starlette.responses import Response

app = FastAPI(title="Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client: redis.Redis = None

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

class MetricsSummary(BaseModel):
    source: str
    total_logs: int
    error_count: int
    warn_count: int
    info_count: int
    timestamp: datetime

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    await redis_client.ping()

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()

@app.get("/api/v1/analytics/summary")
async def get_summary(source: Optional[str] = None):
    """Get aggregated log metrics"""
    if source:
        metrics = await redis_client.hgetall(f"metrics:{source}")
        return {
            "source": source,
            "metrics": metrics,
            "timestamp": datetime.utcnow()
        }
    
    # Get all sources
    keys = await redis_client.keys("metrics:*")
    summaries = []
    for key in keys:
        source_name = key.split(":")[-1]
        metrics = await redis_client.hgetall(key)
        summaries.append({
            "source": source_name,
            "metrics": metrics
        })
    
    return {"summaries": summaries, "timestamp": datetime.utcnow()}

@app.get("/api/v1/analytics/recent-logs")
async def get_recent_logs(limit: int = Query(default=100, le=1000)):
    """Get recent log entries from cache"""
    keys = await redis_client.keys("recent:*")
    keys = sorted(keys, reverse=True)[:limit]
    
    logs = []
    for key in keys:
        log_data = await redis_client.get(key)
        if log_data:
            logs.append(json.loads(log_data))
    
    return {"logs": logs, "count": len(logs)}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
