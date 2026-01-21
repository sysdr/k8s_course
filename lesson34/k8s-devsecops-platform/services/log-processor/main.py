"""
Log Processor Service - Process and store log entries
Implements log parsing, validation, and storage
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import logging
from collections import deque
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_PROCESSED = Counter('logs_processed_total', 'Total logs processed', ['level', 'service'])
PROCESSING_DURATION = Histogram('log_processing_duration_seconds', 'Log processing duration')

app = FastAPI(title="Log Processor Service")

# In-memory log storage (use database in production)
log_store: deque = deque(maxlen=10000)

class LogEntry(BaseModel):
    level: str
    message: str
    service: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    logs_stored: int

class LogStats(BaseModel):
    total_logs: int
    by_level: Dict[str, int]
    by_service: Dict[str, int]

def validate_log_level(level: str) -> bool:
    """Validate log level"""
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    return level.upper() in valid_levels

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        logs_stored=len(log_store)
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/logs")
async def process_log(log_entry: LogEntry):
    """Process and store log entry"""
    # Validate log level
    if not validate_log_level(log_entry.level):
        raise HTTPException(status_code=400, detail="Invalid log level")
    
    # Add timestamp if not provided
    if not log_entry.timestamp:
        log_entry.timestamp = datetime.utcnow().isoformat()
    
    # Store log
    log_store.append(log_entry.dict())
    
    # Record metrics
    LOGS_PROCESSED.labels(
        level=log_entry.level.upper(),
        service=log_entry.service
    ).inc()
    
    logger.info(f"Processed log from {log_entry.service}: {log_entry.level}")
    
    return {"status": "processed", "timestamp": log_entry.timestamp}

@app.get("/logs", response_model=List[LogEntry])
async def get_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100
):
    """Retrieve logs with optional filtering"""
    logs = list(log_store)
    
    # Apply filters
    if service:
        logs = [log for log in logs if log.get("service") == service]
    
    if level:
        logs = [log for log in logs if log.get("level", "").upper() == level.upper()]
    
    # Limit results
    logs = logs[-limit:]
    
    return logs

@app.get("/stats", response_model=LogStats)
async def get_stats():
    """Get log statistics"""
    logs = list(log_store)
    
    by_level: Dict[str, int] = {}
    by_service: Dict[str, int] = {}
    
    for log in logs:
        level = log.get("level", "UNKNOWN").upper()
        service = log.get("service", "unknown")
        
        by_level[level] = by_level.get(level, 0) + 1
        by_service[service] = by_service.get(service, 0) + 1
    
    return LogStats(
        total_logs=len(logs),
        by_level=by_level,
        by_service=by_service
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
