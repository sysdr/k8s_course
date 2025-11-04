from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import os
from collections import Counter
from datetime import datetime, timedelta

app = FastAPI(title="Log Analytics Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis-service"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

@app.get("/analytics/summary")
async def get_summary():
    """Get summary statistics"""
    try:
        logs = redis_client.lrange("logs", 0, -1)
        if not logs:
            return {
                "total_logs": 0,
                "by_level": {},
                "by_source": {},
                "recent_logs": []
            }
        
        log_data = [json.loads(log) for log in logs]
        levels = Counter([log.get("level", "unknown") for log in log_data])
        sources = Counter([log.get("source", "unknown") for log in log_data])
        
        recent = log_data[-10:] if len(log_data) >= 10 else log_data
        
        return {
            "total_logs": len(log_data),
            "by_level": dict(levels),
            "by_source": dict(sources),
            "recent_logs": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/stats")
async def get_stats():
    """Get detailed statistics"""
    try:
        count = int(redis_client.get("log_count") or "0")
        logs = redis_client.lrange("logs", 0, 99)
        log_data = [json.loads(log) for log in logs] if logs else []
        
        return {
            "total_count": count,
            "recent_100": len(log_data),
            "levels": dict(Counter([log.get("level") for log in log_data])),
            "sources": dict(Counter([log.get("source") for log in log_data]))
        }
    except Exception as e:
        return {"error": str(e), "total_count": 0}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "log-analytics"}
