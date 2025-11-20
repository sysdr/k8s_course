"""
Log Collector Service - Demonstrates health probes with fast startup
and graceful shutdown patterns.
"""

import asyncio
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_RECEIVED = Counter('logs_received_total', 'Total logs received')
LOGS_SENT = Counter('logs_sent_total', 'Total logs sent to Kafka')
BUFFER_SIZE = Gauge('log_buffer_size', 'Current buffer size')
PROCESSING_TIME = Histogram('log_processing_seconds', 'Log processing time')

# Application state
class AppState:
    def __init__(self):
        self.kafka_producer: AIOKafkaProducer | None = None
        self.redis_client: redis.Redis | None = None
        self.is_healthy = False
        self.is_ready = False
        self.is_shutting_down = False
        self.buffer: list[dict] = []
        self.buffer_lock = asyncio.Lock()
        self.start_time = time.time()

state = AppState()

# Models
class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str
    metadata: dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    details: dict[str, Any] = {}

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper startup/shutdown."""
    logger.info("Starting Log Collector service...")
    
    # Initialize Kafka producer
    try:
        state.kafka_producer = AIOKafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: str(v).encode('utf-8'),
            acks='all',
            enable_idempotence=True,
            max_batch_size=16384,
            linger_ms=10
        )
        await state.kafka_producer.start()
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {e}")
        state.kafka_producer = None

    # Initialize Redis
    try:
        state.redis_client = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True,
            socket_connect_timeout=5
        )
        await state.redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        state.redis_client = None

    # Mark as healthy (internal state OK)
    state.is_healthy = True
    
    # Mark as ready if dependencies are available
    if state.kafka_producer and state.redis_client:
        state.is_ready = True
        logger.info("Service is ready to accept traffic")
    else:
        logger.warning("Service started but dependencies unavailable")

    # Start buffer flush task
    flush_task = asyncio.create_task(periodic_flush())

    yield

    # Shutdown sequence
    logger.info("Initiating graceful shutdown...")
    state.is_shutting_down = True
    state.is_ready = False

    # Cancel flush task
    flush_task.cancel()
    try:
        await flush_task
    except asyncio.CancelledError:
        pass

    # Flush remaining buffer
    await flush_buffer()
    logger.info("Buffer flushed")

    # Close connections
    if state.kafka_producer:
        await state.kafka_producer.stop()
        logger.info("Kafka producer closed")

    if state.redis_client:
        await state.redis_client.close()
        logger.info("Redis connection closed")

    logger.info("Shutdown complete")

app = FastAPI(
    title="Log Collector Service",
    version="1.0.0",
    lifespan=lifespan
)

async def periodic_flush():
    """Periodically flush buffer to Kafka."""
    while not state.is_shutting_down:
        await asyncio.sleep(5)
        await flush_buffer()

async def flush_buffer():
    """Flush buffered logs to Kafka."""
    async with state.buffer_lock:
        if not state.buffer or not state.kafka_producer:
            return
        
        logs_to_send = state.buffer.copy()
        state.buffer.clear()
        BUFFER_SIZE.set(0)

    for log in logs_to_send:
        try:
            await state.kafka_producer.send_and_wait(
                'logs',
                value=str(log)
            )
            LOGS_SENT.inc()
        except Exception as e:
            logger.error(f"Failed to send log to Kafka: {e}")
            # Re-buffer failed logs
            async with state.buffer_lock:
                state.buffer.append(log)
                BUFFER_SIZE.set(len(state.buffer))

# Health check endpoints
@app.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    """
    Liveness probe - checks if process is fundamentally healthy.
    Only checks internal state, NOT external dependencies.
    """
    if not state.is_healthy:
        raise HTTPException(
            status_code=503,
            detail="Service is not healthy"
        )
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        details={
            "uptime_seconds": time.time() - state.start_time,
            "is_shutting_down": state.is_shutting_down
        }
    )

@app.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness probe - checks if service can handle traffic.
    Checks external dependencies (Kafka, Redis).
    """
    if state.is_shutting_down:
        raise HTTPException(
            status_code=503,
            detail="Service is shutting down"
        )
    
    if not state.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Service is not ready"
        )

    # Verify dependencies are still available
    kafka_ok = state.kafka_producer is not None
    redis_ok = False
    
    if state.redis_client:
        try:
            await state.redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    if not kafka_ok or not redis_ok:
        state.is_ready = False
        raise HTTPException(
            status_code=503,
            detail=f"Dependencies unavailable: kafka={kafka_ok}, redis={redis_ok}"
        )

    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        details={
            "kafka_connected": kafka_ok,
            "redis_connected": redis_ok,
            "buffer_size": len(state.buffer)
        }
    )

@app.get("/health/startup", response_model=HealthResponse)
async def startup_check():
    """
    Startup probe - checks if application has finished initializing.
    """
    if state.is_healthy:
        return HealthResponse(
            status="started",
            timestamp=datetime.utcnow().isoformat(),
            details={"initialization_complete": True}
        )
    
    raise HTTPException(
        status_code=503,
        detail="Service is still initializing"
    )

# Shutdown endpoint for preStop hook
@app.post("/shutdown")
async def initiate_shutdown():
    """
    Called by Kubernetes preStop hook to initiate graceful shutdown.
    """
    logger.info("Received shutdown signal via preStop hook")
    state.is_shutting_down = True
    state.is_ready = False
    
    # Flush buffer before responding
    await flush_buffer()
    
    return {"status": "shutdown_initiated", "buffer_flushed": True}

# Business endpoints
@app.post("/logs")
async def collect_log(entry: LogEntry):
    """Receive and buffer log entries."""
    if state.is_shutting_down:
        raise HTTPException(
            status_code=503,
            detail="Service is shutting down"
        )
    
    if not state.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Service is not ready"
        )

    with PROCESSING_TIME.time():
        LOGS_RECEIVED.inc()
        
        log_data = entry.model_dump()
        log_data['collected_at'] = datetime.utcnow().isoformat()
        
        async with state.buffer_lock:
            state.buffer.append(log_data)
            BUFFER_SIZE.set(len(state.buffer))
            
            # Flush if buffer is large
            if len(state.buffer) >= 100:
                asyncio.create_task(flush_buffer())

    return {"status": "accepted", "buffer_size": len(state.buffer)}

@app.post("/logs/batch")
async def collect_logs_batch(entries: list[LogEntry]):
    """Receive batch of log entries."""
    if state.is_shutting_down or not state.is_ready:
        raise HTTPException(status_code=503, detail="Service unavailable")

    with PROCESSING_TIME.time():
        for entry in entries:
            LOGS_RECEIVED.inc()
            log_data = entry.model_dump()
            log_data['collected_at'] = datetime.utcnow().isoformat()
            
            async with state.buffer_lock:
                state.buffer.append(log_data)
        
        BUFFER_SIZE.set(len(state.buffer))

    return {"status": "accepted", "count": len(entries)}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import Response
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
