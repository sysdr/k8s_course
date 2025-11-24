import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any
import redis.asyncio as redis
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Parser Service")

# Redis connection
redis_client: redis.Redis = None

# Parsing patterns
LOG_PATTERNS = {
    "timestamp": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
    "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    "error_code": r"(4\d{2}|5\d{2})",
    "duration": r"duration=(\d+\.?\d*)(ms|s)",
}

# Metrics
metrics = {
    "logs_processed": 0,
    "logs_failed": 0,
    "processing_time_ms": 0
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
            socket_keepalive=True
        )
        await redis_client.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        
        # Start background parser
        asyncio.create_task(parse_logs_worker())
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

async def parse_log_entry(log_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and enrich log entry with extracted data"""
    start_time = datetime.now()
    
    parsed = {
        "original": log_data,
        "parsed": {},
        "enriched_at": datetime.utcnow().isoformat()
    }
    
    message = log_data.get("message", "")
    
    # Extract patterns
    for pattern_name, pattern in LOG_PATTERNS.items():
        matches = re.findall(pattern, message)
        if matches:
            parsed["parsed"][pattern_name] = matches
    
    # Categorize log level
    level = log_data.get("level", "INFO")
    parsed["parsed"]["severity"] = {
        "DEBUG": 1,
        "INFO": 2,
        "WARNING": 3,
        "ERROR": 4,
        "CRITICAL": 5
    }.get(level, 2)
    
    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    parsed["processing_time_ms"] = processing_time
    
    return parsed

async def parse_logs_worker():
    """Background worker that processes logs from queue"""
    logger.info("Starting log parser worker...")
    
    while True:
        try:
            if redis_client is None:
                await asyncio.sleep(5)
                continue
            
            # Blocking pop from queue (timeout 5 seconds)
            result = await redis_client.blpop("log_queue", timeout=5)
            
            if result is None:
                continue
            
            _, log_json = result
            log_data = json.loads(log_json)
            
            # Parse the log
            parsed_log = await parse_log_entry(log_data)
            
            # Store parsed log
            await redis_client.rpush("parsed_logs", json.dumps(parsed_log))
            
            metrics["logs_processed"] += 1
            metrics["processing_time_ms"] = (
                metrics["processing_time_ms"] * 0.9 + 
                parsed_log["processing_time_ms"] * 0.1
            )
            
            if metrics["logs_processed"] % 100 == 0:
                logger.info(f"Processed {metrics['logs_processed']} logs")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in queue: {e}")
            metrics["logs_failed"] += 1
        except Exception as e:
            logger.error(f"Error processing log: {e}")
            metrics["logs_failed"] += 1
            await asyncio.sleep(1)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "log-parser"}

@app.get("/ready")
async def ready():
    if redis_client is None:
        return {"status": "not ready", "reason": "Redis not connected"}, 503
    try:
        await redis_client.ping()
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready", "reason": "Redis unreachable"}, 503

@app.get("/metrics")
async def get_metrics():
    queue_length = 0
    if redis_client:
        try:
            queue_length = await redis_client.llen("log_queue")
        except:
            pass
    
    return {
        **metrics,
        "queue_length": queue_length
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
