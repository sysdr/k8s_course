"""
Analytics API Service - Demonstrates health probes for high-availability
user-facing service with graceful shutdown and connection draining.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Query
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
REQUESTS_TOTAL = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('api_active_connections', 'Active connections')
DB_POOL_SIZE = Gauge('db_connection_pool_size', 'Database pool size')

class AppState:
    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.is_healthy = False
        self.is_ready = False
        self.is_shutting_down = False
        self.startup_complete = False
        self.start_time = time.time()
        self.active_requests = 0
        # Simulated connection pool
        self.db_pool_available = 10
        self.db_pool_total = 10

state = AppState()

class LogSummary(BaseModel):
    total_logs: int
    by_level: dict[str, int]
    by_service: dict[str, int]
    time_range: dict[str, str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    details: dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Analytics API service...")
    
    state.is_healthy = True
    
    # Connect to Redis
    try:
        state.redis_client = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True,
            socket_connect_timeout=5,
            max_connections=20
        )
        await state.redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    state.startup_complete = True
    
    # Ready when dependencies available
    if state.redis_client:
        state.is_ready = True
        logger.info("Service is ready")
    
    yield
    
    # Graceful shutdown
    logger.info("Starting graceful shutdown...")
    state.is_shutting_down = True
    state.is_ready = False
    
    # Wait for active requests to complete (max 25s)
    shutdown_start = time.time()
    while state.active_requests > 0 and (time.time() - shutdown_start) < 25:
        logger.info(f"Waiting for {state.active_requests} active requests...")
        await asyncio.sleep(1)
    
    if state.redis_client:
        await state.redis_client.close()
    
    logger.info("Shutdown complete")

app = FastAPI(
    title="Analytics API Service",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def track_requests(request, call_next):
    """Track active requests for graceful shutdown."""
    state.active_requests += 1
    ACTIVE_CONNECTIONS.set(state.active_requests)
    
    try:
        response = await call_next(request)
        return response
    finally:
        state.active_requests -= 1
        ACTIVE_CONNECTIONS.set(state.active_requests)

@app.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    """
    Liveness probe - checks internal health only.
    Never checks external dependencies for liveness!
    """
    if not state.is_healthy:
        raise HTTPException(status_code=503, detail="Unhealthy")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        details={
            "uptime_seconds": time.time() - state.start_time
        }
    )

@app.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness probe - checks if service can handle requests.
    Checks database connection pool health.
    """
    if state.is_shutting_down:
        raise HTTPException(status_code=503, detail="Shutting down")
    
    if not state.is_ready:
        raise HTTPException(status_code=503, detail="Not ready")
    
    # Check database pool health
    pool_utilization = 1 - (state.db_pool_available / state.db_pool_total)
    DB_POOL_SIZE.set(state.db_pool_available)
    
    # Mark not ready if pool exhausted
    if state.db_pool_available < 2:
        raise HTTPException(
            status_code=503,
            detail=f"Connection pool exhausted: {state.db_pool_available}/{state.db_pool_total}"
        )
    
    # Check Redis connectivity
    redis_ok = False
    if state.redis_client:
        try:
            await state.redis_client.ping()
            redis_ok = True
        except Exception:
            pass
    
    if not redis_ok:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        details={
            "redis_connected": redis_ok,
            "pool_available": state.db_pool_available,
            "pool_utilization": f"{pool_utilization:.1%}",
            "active_requests": state.active_requests
        }
    )

@app.get("/health/startup", response_model=HealthResponse)
async def startup_check():
    """Startup probe for initialization verification."""
    if state.startup_complete:
        return HealthResponse(
            status="started",
            timestamp=datetime.utcnow().isoformat()
        )
    
    raise HTTPException(status_code=503, detail="Still initializing")

@app.post("/shutdown")
async def graceful_shutdown():
    """
    PreStop hook endpoint for graceful shutdown.
    Marks service not ready and waits for connection draining.
    """
    logger.info("Received shutdown signal")
    state.is_ready = False
    
    # Sleep to allow load balancer to update
    await asyncio.sleep(5)
    
    return {
        "status": "draining",
        "active_requests": state.active_requests
    }

@app.get("/api/logs/summary", response_model=LogSummary)
async def get_log_summary(
    hours: int = Query(default=24, ge=1, le=168)
):
    """Get summary of processed logs."""
    REQUESTS_TOTAL.labels(endpoint="/api/logs/summary", status="success").inc()
    
    with REQUEST_DURATION.time():
        if not state.redis_client:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Simulate connection pool usage
        state.db_pool_available -= 1
        try:
            # Get processed logs from Redis
            logs = await state.redis_client.lrange("processed_logs", 0, 999)
            
            by_level: dict[str, int] = {}
            by_service: dict[str, int] = {}
            
            for log_json in logs:
                try:
                    import json
                    log = json.loads(log_json)
                    original = log.get("original", {})
                    
                    level = original.get("level", "unknown")
                    service = original.get("service", "unknown")
                    
                    by_level[level] = by_level.get(level, 0) + 1
                    by_service[service] = by_service.get(service, 0) + 1
                except Exception:
                    continue
            
            return LogSummary(
                total_logs=len(logs),
                by_level=by_level,
                by_service=by_service,
                time_range={
                    "start": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            )
        finally:
            state.db_pool_available += 1

@app.get("/api/logs/recent")
async def get_recent_logs(limit: int = Query(default=100, ge=1, le=1000)):
    """Get recent processed logs."""
    REQUESTS_TOTAL.labels(endpoint="/api/logs/recent", status="success").inc()
    
    if not state.redis_client:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    logs = await state.redis_client.lrange("processed_logs", 0, limit - 1)
    
    import json
    return {
        "logs": [json.loads(log) for log in logs],
        "count": len(logs)
    }

@app.get("/api/logs/anomalies")
async def get_anomalies(threshold: float = Query(default=0.5, ge=0, le=1)):
    """Get logs with high anomaly scores."""
    REQUESTS_TOTAL.labels(endpoint="/api/logs/anomalies", status="success").inc()
    
    if not state.redis_client:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    logs = await state.redis_client.lrange("processed_logs", 0, 999)
    
    import json
    anomalies = []
    for log_json in logs:
        try:
            log = json.loads(log_json)
            if log.get("anomaly_score", 0) >= threshold:
                anomalies.append(log)
        except Exception:
            continue
    
    return {
        "anomalies": anomalies,
        "count": len(anomalies),
        "threshold": threshold
    }

@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
