import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import redis.asyncio as redis
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Engine")

redis_client: redis.Redis = None

# In-memory analytics cache
analytics_cache = {
    "total_logs": 0,
    "logs_by_level": defaultdict(int),
    "logs_by_service": defaultdict(int),
    "error_rate": 0.0,
    "last_updated": datetime.utcnow().isoformat()
}

# Timeseries data (keep last 12 data points = 2 minutes at 10s intervals)
timeseries_data = {
    "timestamps": [],
    "error_rates": [],
    "total_logs": []
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
            decode_responses=True
        )
        await redis_client.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        
        # Start analytics worker
        asyncio.create_task(analytics_worker())
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

async def compute_analytics(parsed_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute analytics from parsed logs"""
    total = len(parsed_logs)
    by_level = defaultdict(int)
    by_service = defaultdict(int)
    error_count = 0
    
    for log in parsed_logs:
        original = log.get("original", {})
        level = original.get("level", "INFO")
        service = original.get("service", "unknown")
        
        by_level[level] += 1
        by_service[service] += 1
        
        if level in ("ERROR", "CRITICAL"):
            error_count += 1
    
    error_rate = (error_count / total * 100) if total > 0 else 0.0
    
    return {
        "total_logs": total,
        "logs_by_level": dict(by_level),
        "logs_by_service": dict(by_service),
        "error_rate": round(error_rate, 2),
        "last_updated": datetime.utcnow().isoformat()
    }

async def analytics_worker():
    """Background worker that computes analytics"""
    logger.info("Starting analytics worker...")
    
    while True:
        try:
            if redis_client is None:
                await asyncio.sleep(10)
                continue
            
            # Get all parsed logs
            logs_json = await redis_client.lrange("parsed_logs", 0, -1)
            
            if not logs_json:
                await asyncio.sleep(10)
                continue
            
            parsed_logs = [json.loads(log) for log in logs_json]
            
            # Compute analytics
            analytics = await compute_analytics(parsed_logs)
            
            # Update cache
            analytics_cache.update(analytics)
            
            # Store in Redis for API access
            await redis_client.set("analytics:current", json.dumps(analytics))
            
            # Update timeseries data (keep last 12 points)
            now = datetime.utcnow()
            timeseries_data["timestamps"].append(now.isoformat())
            timeseries_data["error_rates"].append(analytics["error_rate"])
            timeseries_data["total_logs"].append(analytics["total_logs"])
            
            # Keep only last 12 data points
            if len(timeseries_data["timestamps"]) > 12:
                timeseries_data["timestamps"] = timeseries_data["timestamps"][-12:]
                timeseries_data["error_rates"] = timeseries_data["error_rates"][-12:]
                timeseries_data["total_logs"] = timeseries_data["total_logs"][-12:]
            
            logger.info(f"Updated analytics: {analytics['total_logs']} logs, {analytics['error_rate']}% errors")
            
            # Trim old logs (keep last 10000)
            if len(parsed_logs) > 10000:
                await redis_client.ltrim("parsed_logs", -10000, -1)
            
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in analytics worker: {e}")
            await asyncio.sleep(5)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics-engine"}

@app.get("/ready")
async def ready():
    if redis_client is None:
        return {"status": "not ready", "reason": "Redis not connected"}, 503
    try:
        await redis_client.ping()
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready", "reason": "Redis unreachable"}, 503

@app.get("/analytics")
async def get_analytics():
    """Get current analytics"""
    return analytics_cache

@app.get("/analytics/timeseries")
async def get_timeseries():
    """Get time-series analytics data"""
    # Return actual historical data points
    # If we don't have enough data yet, pad with current values
    if len(timeseries_data["timestamps"]) < 12:
        # Pad with current values for missing data points
        current_time = datetime.utcnow()
        timestamps = timeseries_data["timestamps"].copy()
        error_rates = timeseries_data["error_rates"].copy()
        total_logs = timeseries_data["total_logs"].copy()
        
        # Fill remaining slots with current values
        while len(timestamps) < 12:
            minutes_ago = 12 - len(timestamps)
            timestamps.insert(0, (current_time - timedelta(minutes=minutes_ago * 5)).isoformat())
            error_rates.insert(0, analytics_cache["error_rate"])
            total_logs.insert(0, analytics_cache["total_logs"])
        
        return {
            "timestamps": timestamps,
            "error_rates": error_rates,
            "total_logs": total_logs
        }
    
    return {
        "timestamps": timeseries_data["timestamps"],
        "error_rates": timeseries_data["error_rates"],
        "total_logs": timeseries_data["total_logs"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
