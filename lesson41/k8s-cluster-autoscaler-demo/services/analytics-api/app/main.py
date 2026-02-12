import json
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis
import structlog
from prometheus_client import generate_latest

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(title="Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

class LogEntry(BaseModel):
    level: str = Field(..., pattern="^(DEBUG|INFO|WARN|ERROR|FATAL)$")
    message: str = Field(..., min_length=1, max_length=10000)
    service: str = Field(..., min_length=1, max_length=100)
    timestamp: Optional[float] = None
    metadata: Optional[dict] = None

@app.get("/api/v1/analytics/summary")
async def get_summary() -> Dict:
    """Get overall log analytics summary"""
    try:
        # Always calculate from recent logs for accuracy
        recent_logs = redis_client.lrange("recent_logs", 0, -1)
        total = len(recent_logs)
        
        # Recalculate counts from recent logs
        level_counts = {"DEBUG": 0, "INFO": 0, "WARN": 0, "ERROR": 0, "FATAL": 0}
        for log_str in recent_logs:
            try:
                log = json.loads(log_str)
                level = log.get('level', 'INFO')
                if level in level_counts:
                    level_counts[level] += 1
            except Exception as e:
                logger.warning("failed_to_parse_log", error=str(e))
                continue
        
        # Also try to get from counters and merge (use max to handle inconsistencies)
        counter_total = int(redis_client.get("total_logs_processed") or 0)
        if counter_total > total:
            total = counter_total
        
        # Merge counter values with calculated values (use max)
        counter_debug = int(redis_client.get("log_count:DEBUG") or 0)
        counter_info = int(redis_client.get("log_count:INFO") or 0)
        counter_warn = int(redis_client.get("log_count:WARN") or 0)
        counter_error = int(redis_client.get("log_count:ERROR") or 0)
        counter_fatal = int(redis_client.get("log_count:FATAL") or 0)
        
        summary = {
            "total_processed": max(total, counter_total),
            "by_level": {
                "DEBUG": max(level_counts["DEBUG"], counter_debug),
                "INFO": max(level_counts["INFO"], counter_info),
                "WARN": max(level_counts["WARN"], counter_warn),
                "ERROR": max(level_counts["ERROR"], counter_error),
                "FATAL": max(level_counts["FATAL"], counter_fatal),
            }
        }
        return summary
    except Exception as e:
        logger.error("summary_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch summary")

@app.get("/api/v1/analytics/services")
async def get_service_stats() -> Dict:
    """Get per-service statistics"""
    try:
        services = {}
        for key in redis_client.scan_iter("service_stats:*"):
            service_name = key.replace("service_stats:", "")
            stats = redis_client.hgetall(key)
            services[service_name] = {k: int(v) for k, v in stats.items()}
        
        return {"services": services}
    except Exception as e:
        logger.error("service_stats_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch service stats")

@app.get("/api/v1/analytics/recent")
async def get_recent_logs(limit: int = 20) -> List[Dict]:
    """Get recent logs (most recent first)"""
    try:
        # Get logs from Redis list (newest are at index 0 due to LPUSH)
        logs = redis_client.lrange("recent_logs", 0, limit - 1)
        # Parse and return (already in reverse chronological order)
        parsed_logs = []
        for log in logs:
            try:
                parsed_logs.append(json.loads(log))
            except Exception as e:
                logger.warning("failed_to_parse_log", error=str(e))
                continue
        return parsed_logs
    except Exception as e:
        logger.error("recent_logs_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch recent logs")

@app.get("/api/v1/analytics/errors")
async def get_recent_errors(limit: int = 10) -> List[Dict]:
    """Get recent error logs"""
    try:
        errors = redis_client.zrevrange("error_logs", 0, limit - 1)
        return [json.loads(error) for error in errors]
    except Exception as e:
        logger.error("errors_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch errors")

@app.post("/api/v1/logs")
async def ingest_log(log_entry: LogEntry):
    """Ingest log directly to Redis (workaround when Kafka is unavailable)"""
    try:
        # Add timestamp if not provided
        if not log_entry.timestamp:
            log_entry.timestamp = time.time()
        
        log_data = log_entry.model_dump()
        log_data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(log_data['timestamp']))
        
        # Store in recent logs
        redis_client.lpush("recent_logs", json.dumps(log_data))
        redis_client.ltrim("recent_logs", 0, 99)  # Keep last 100 logs
        
        # Update counters
        redis_client.incr(f"log_count:{log_entry.level}")
        redis_client.incr("total_logs_processed")
        
        # Update service statistics
        redis_client.hincrby(f"service_stats:{log_entry.service}", log_entry.level, 1)
        redis_client.hincrby(f"service_stats:{log_entry.service}", "total", 1)
        
        # Store error logs separately
        if log_entry.level in ['ERROR', 'FATAL']:
            redis_client.zadd(
                "error_logs",
                {json.dumps(log_data): time.time()}
            )
            # Keep only last 1000 error logs
            redis_client.zremrangebyrank("error_logs", 0, -1001)
        
        logger.info("log_ingested", level=log_entry.level, service=log_entry.service)
        
        return {"status": "accepted", "id": str(int(time.time() * 1000))}
    
    except Exception as e:
        logger.error("log_ingestion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to ingest log: {str(e)}")

@app.get("/health")
async def health_check():
    redis_client.ping()
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
