"""
Log Ingestion Service - High-throughput log entry point
Validates, enriches, and queues logs for processing
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import logging
import asyncio
import time
from datetime import datetime
import json
import os
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Ingestion Service", version="1.0.0")

# In-memory buffer (in production, use Redis or Kafka)
log_buffer = asyncio.Queue(maxsize=10000)
ingestion_stats = {
    "total_logs": 0,
    "success": 0,
    "failed": 0,
    "buffer_size": 0
}

class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Level must be one of {valid_levels}')
        return v.upper()

@app.get("/health")
async def health_check():
    """Health check for Kubernetes probes"""
    buffer_size = log_buffer.qsize()
    
    # Unhealthy if buffer is nearly full
    status = "healthy" if buffer_size < 8000 else "degraded"
    
    return {
        "status": status,
        "service": "log-ingestion",
        "timestamp": datetime.utcnow().isoformat(),
        "buffer_size": buffer_size,
        "max_buffer_size": 10000
    }

@app.post("/ingest", status_code=201)
async def ingest_log(log_entry: LogEntry):
    """
    Ingest log entry into processing queue
    High-throughput endpoint designed for 10k+ requests/second
    """
    try:
        # Enrich log with ingestion metadata
        enriched_log = log_entry.dict()
        enriched_log["ingestion_timestamp"] = datetime.utcnow().isoformat()
        enriched_log["ingestion_service"] = "log-ingestion-v1"
        
        # Non-blocking queue put with timeout
        try:
            await asyncio.wait_for(
                log_buffer.put(enriched_log),
                timeout=1.0
            )
            ingestion_stats["success"] += 1
            ingestion_stats["total_logs"] += 1
            
        except asyncio.TimeoutError:
            ingestion_stats["failed"] += 1
            raise HTTPException(
                status_code=503,
                detail="Ingestion buffer full, retry later"
            )
        
        return {
            "status": "accepted",
            "log_id": f"{log_entry.service}-{int(time.time() * 1000)}",
            "buffer_position": log_buffer.qsize()
        }
        
    except Exception as e:
        ingestion_stats["failed"] += 1
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get ingestion statistics"""
    ingestion_stats["buffer_size"] = log_buffer.qsize()
    return ingestion_stats

@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    from fastapi.responses import Response
    buffer_size = log_buffer.qsize()
    metrics_text = f"""# HELP log_ingestion_total Total logs ingested
# TYPE log_ingestion_total counter
log_ingestion_total{{service="log-ingestion"}} {ingestion_stats["total_logs"]}
# HELP log_ingestion_success Successful log ingestions
# TYPE log_ingestion_success counter
log_ingestion_success{{service="log-ingestion"}} {ingestion_stats["success"]}
# HELP log_ingestion_failed Failed log ingestions
# TYPE log_ingestion_failed counter
log_ingestion_failed{{service="log-ingestion"}} {ingestion_stats["failed"]}
# HELP log_ingestion_buffer_size Current buffer size
# TYPE log_ingestion_buffer_size gauge
log_ingestion_buffer_size{{service="log-ingestion"}} {buffer_size}
"""
    return Response(content=metrics_text, media_type="text/plain")

# Background task to process buffer
@app.on_event("startup")
async def startup_event():
    """Start background processing tasks"""
    asyncio.create_task(process_buffer())
    logger.info("Log Ingestion Service started")

async def process_buffer():
    """Background task to forward logs to processor service"""
    processor_url = os.getenv("LOG_PROCESSOR_URL", "http://log-processor:8080")
    client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    
    while True:
        try:
            # Get batch of logs
            batch = []
            for _ in range(100):
                if not log_buffer.empty():
                    batch.append(await asyncio.wait_for(log_buffer.get(), timeout=0.1))
                else:
                    break
            
            if batch:
                logger.info(f"Processing batch of {len(batch)} logs")
                # Send each log to processor service
                for log_data in batch:
                    try:
                        response = await client.post(
                            f"{processor_url}/process",
                            json=log_data,
                            timeout=5.0
                        )
                        response.raise_for_status()
                    except Exception as e:
                        logger.error(f"Failed to send log to processor: {e}")
            
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Buffer processing error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
