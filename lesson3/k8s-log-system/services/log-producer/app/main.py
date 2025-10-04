import asyncio
import random
import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Producer Service")

# Prometheus metrics
logs_generated = Counter('logs_generated_total', 'Total logs generated')
log_latency = Histogram('log_generation_latency_seconds', 'Log generation latency')
send_errors = Counter('log_send_errors_total', 'Total errors sending logs')

# Configuration from environment
PROCESSOR_URL = os.getenv('PROCESSOR_URL', 'http://log-processor:8080')
LOG_RATE = int(os.getenv('LOG_RATE', '10'))  # logs per second

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str
    service: str
    message: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LogStats(BaseModel):
    total_generated: int
    current_rate: float
    processor_healthy: bool

# Log templates for realistic data
LOG_TEMPLATES = [
    {"level": "INFO", "service": "api-gateway", "message": "Request processed successfully"},
    {"level": "INFO", "service": "auth-service", "message": "User authenticated"},
    {"level": "WARNING", "service": "payment-service", "message": "Payment retry attempt"},
    {"level": "ERROR", "service": "database", "message": "Connection pool exhausted"},
    {"level": "INFO", "service": "cache", "message": "Cache hit"},
    {"level": "WARNING", "service": "api-gateway", "message": "Rate limit approaching"},
    {"level": "ERROR", "service": "email-service", "message": "SMTP connection failed"},
    {"level": "INFO", "service": "notification", "message": "Push notification sent"},
]

stats = {
    "total": 0,
    "rate": 0.0,
    "processor_healthy": True
}

async def check_processor_health():
    """Check if log processor is healthy"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PROCESSOR_URL}/health", timeout=2.0)
            stats["processor_healthy"] = response.status_code == 200
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Processor health check failed: {e}")
        stats["processor_healthy"] = False
        return False

async def generate_log() -> LogEntry:
    """Generate a realistic log entry"""
    template = random.choice(LOG_TEMPLATES)
    return LogEntry(
        level=template["level"],
        service=template["service"],
        message=template["message"],
        trace_id=f"trace-{random.randint(1000, 9999)}",
        user_id=f"user-{random.randint(1, 1000)}"
    )

async def send_log(log_entry: LogEntry):
    """Send log to processor service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PROCESSOR_URL}/logs",
                json=json.loads(log_entry.json()),
                timeout=5.0
            )
            if response.status_code == 200:
                logs_generated.inc()
                stats["total"] += 1
            else:
                send_errors.inc()
                logger.error(f"Failed to send log: {response.status_code}")
    except Exception as e:
        send_errors.inc()
        logger.error(f"Error sending log: {e}")

async def log_generator():
    """Background task to generate logs continuously"""
    while True:
        try:
            with log_latency.time():
                log_entry = await generate_log()
                await send_log(log_entry)
            
            # Rate limiting
            await asyncio.sleep(1.0 / LOG_RATE)
        except Exception as e:
            logger.error(f"Error in log generator: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Start background log generation"""
    asyncio.create_task(log_generator())
    asyncio.create_task(periodic_health_check())
    logger.info(f"Log producer started - generating {LOG_RATE} logs/second")

async def periodic_health_check():
    """Periodically check processor health"""
    while True:
        await check_processor_health()
        await asyncio.sleep(30)

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy", "processor_connected": stats["processor_healthy"]}

@app.get("/ready")
async def readiness_check():
    """Readiness check - only ready if processor is reachable"""
    if await check_processor_health():
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Processor not available")

@app.get("/stats")
async def get_stats() -> LogStats:
    """Get log generation statistics"""
    return LogStats(
        total_generated=stats["total"],
        current_rate=LOG_RATE,
        processor_healthy=stats["processor_healthy"]
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
