"""
FastAPI Log Processor with Prometheus Metrics
Intentionally configured with metric naming mismatches for debugging exercise
"""
import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus Metrics - Intentional naming that doesn't match Grafana queries
# Clear registry to prevent duplicate registration on module reload
from prometheus_client import REGISTRY, CollectorRegistry

# Clear any existing collectors to prevent duplicate registration
try:
    REGISTRY._collector_to_names.clear()
    REGISTRY._names_to_collectors.clear()
except:
    pass

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint', 'status_code']
)

log_entries_processed = Counter(
    'log_entries_processed_total',
    'Total number of log entries processed',
    ['severity', 'source']
)

active_processing_jobs = Gauge(
    'active_processing_jobs',
    'Number of log processing jobs currently running'
)

# Business metrics
log_parse_errors = Counter(
    'log_parse_errors_total',
    'Total number of log parsing failures',
    ['error_type']
)

storage_queue_size = Gauge(
    'storage_queue_size_bytes',
    'Size of storage queue in bytes'
)

# Data models
class LogEntry(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    level: str = Field(..., description="Log severity level")
    message: str
    source: str = Field(default="unknown")
    metadata: Dict[str, str] = Field(default_factory=dict)

class ProcessingStatus(BaseModel):
    entries_processed: int
    active_jobs: int
    queue_size: int
    error_rate: float

# In-memory storage for demonstration
log_storage: List[LogEntry] = []
processing_stats = {
    'total_processed': 0,
    'total_errors': 0,
    'active_jobs': 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting log processor application")
    # Simulate background processing
    asyncio.create_task(simulate_background_processing())
    yield
    logger.info("Shutting down log processor application")

app = FastAPI(
    title="Log Processor Service",
    description="Processes and analyzes log entries with Prometheus metrics",
    version="1.0.0",
    lifespan=lifespan
)

async def simulate_background_processing():
    """Simulate continuous log processing to generate metrics"""
    while True:
        await asyncio.sleep(random.uniform(1, 5))
        
        # Simulate processing load
        active_processing_jobs.set(random.randint(0, 10))
        storage_queue_size.set(random.randint(1000, 50000))
        
        # Randomly generate errors
        if random.random() < 0.1:
            error_type = random.choice(['parse_error', 'validation_error', 'timeout'])
            log_parse_errors.labels(error_type=error_type).inc()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).observe(duration)
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=500
        ).observe(duration)
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Check if background processing is functioning
    is_ready = processing_stats['active_jobs'] < 100
    
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready", "timestamp": time.time()}

@app.post("/logs/ingest")
async def ingest_logs(entry: LogEntry):
    """Ingest a single log entry"""
    try:
        log_storage.append(entry)
        processing_stats['total_processed'] += 1
        
        # Track metric by severity and source
        log_entries_processed.labels(
            severity=entry.level,
            source=entry.source
        ).inc()
        
        logger.info(f"Processed log entry: {entry.level} from {entry.source}")
        
        return {
            "status": "accepted",
            "entry_id": len(log_storage) - 1
        }
    except Exception as e:
        processing_stats['total_errors'] += 1
        log_parse_errors.labels(error_type='ingestion_error').inc()
        logger.error(f"Failed to ingest log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/stats", response_model=ProcessingStatus)
async def get_processing_stats():
    """Get current processing statistics"""
    total = processing_stats['total_processed']
    errors = processing_stats['total_errors']
    error_rate = (errors / total * 100) if total > 0 else 0.0
    
    return ProcessingStatus(
        entries_processed=total,
        active_jobs=processing_stats['active_jobs'],
        queue_size=len(log_storage),
        error_rate=error_rate
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint - exposed on port 8080"""
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "log-processor",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "ingest": "/logs/ingest",
            "stats": "/logs/stats",
            "metrics": "/metrics"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
