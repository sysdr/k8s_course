"""
API Gateway v3 - Experimental Version with ML-Powered Rate Limiting
Predictive rate limiting based on user behavior patterns
"""
import asyncio
import logging
import os
import time
import json
import random
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Clear any existing metrics in the registry to avoid duplicates
try:
    collectors_to_remove = list(REGISTRY._collector_to_names.keys())
    for collector in collectors_to_remove:
        try:
            REGISTRY.unregister(collector)
        except (KeyError, ValueError, AttributeError):
            pass
except (AttributeError, KeyError, TypeError):
    try:
        REGISTRY.clear()
    except (AttributeError, TypeError):
        pass

# Helper function to safely get or create metrics
def safe_metric(metric_class, name, documentation, labelnames=None):
    """Safely get existing metric or create new one"""
    # Simple approach: just try to create, catch error and return dummy
    try:
        return metric_class(name, documentation, labelnames or [])
    except (ValueError, KeyError) as e:
        # If creation fails due to duplicate, return dummy metric
        logger.warning(f"Could not create metric {name}: {e}, using dummy metric")
        class DummyMetric:
            def labels(self, **kwargs): return self
            def inc(self, value=1): pass
            def observe(self, value): pass
            def dec(self, value=1): pass
        return DummyMetric()

REQUEST_COUNT = safe_metric(
    Counter, 'api_gateway_requests_total',
    'Total API gateway requests',
    ['method', 'endpoint', 'status', 'version']
)
REQUEST_DURATION = safe_metric(
    Histogram, 'api_gateway_request_duration_seconds',
    'API gateway request duration',
    ['method', 'endpoint', 'version']
)
ACTIVE_CONNECTIONS = safe_metric(
    Gauge, 'api_gateway_active_connections',
    'Active connections',
    ['version']
)
ML_PREDICTIONS = safe_metric(
    Counter, 'api_gateway_ml_predictions_total',
    'ML rate limit predictions',
    ['version', 'prediction']
)

VERSION = "v3"
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8080")

redis_client: Optional[redis.Redis] = None
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, http_client
    
    logger.info(f"Starting API Gateway {VERSION} with ML rate limiting")
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5
    )
    http_client = httpx.AsyncClient(timeout=10.0)
    
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    yield
    
    logger.info("Shutting down API Gateway")
    if redis_client:
        await redis_client.close()
    if http_client:
        await http_client.aclose()

app = FastAPI(
    title=f"API Gateway {VERSION}",
    version=VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    ACTIVE_CONNECTIONS.labels(version=VERSION).inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            version=VERSION
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
            version=VERSION
        ).observe(duration)
        
        response.headers["X-Api-Version"] = VERSION
        response.headers["X-Request-Duration"] = f"{duration:.3f}"
        response.headers["X-Rate-Limit-Strategy"] = "ml-powered"
        
        return response
    finally:
        ACTIVE_CONNECTIONS.labels(version=VERSION).dec()

async def ml_rate_limit_check(user_id: str, tier: str) -> Dict[str, Any]:
    """
    ML-powered rate limiting based on user behavior patterns
    In production, this would use a trained model
    """
    # Simulate ML prediction
    await asyncio.sleep(0.01)  # Model inference time
    
    # Get user's request history
    history_key = f"ml:history:{user_id}"
    try:
        if redis_client:
            history = await redis_client.lrange(history_key, 0, 99)
            request_count = len(history)
            
            # Simple heuristic (in production, use trained model)
            # Predict if user is likely to abuse rate limits
            abuse_score = min(request_count / 100, 1.0)
            is_suspicious = abuse_score > 0.8
            
            if is_suspicious:
                ML_PREDICTIONS.labels(version=VERSION, prediction="suspicious").inc()
                # More restrictive limits for suspicious users
                limit = 50
            else:
                ML_PREDICTIONS.labels(version=VERSION, prediction="normal").inc()
                # Standard limits based on tier
                limits = {"free": 100, "premium": 1000, "enterprise": 10000}
                limit = limits.get(tier, 100)
            
            remaining = max(0, limit - request_count)
            allowed = remaining > 0
            
            # Track this request
            await redis_client.lpush(history_key, datetime.utcnow().isoformat())
            await redis_client.ltrim(history_key, 0, 99)
            await redis_client.expire(history_key, 3600)
            
            return {
                "allowed": allowed,
                "remaining": remaining,
                "limit": limit,
                "ml_score": abuse_score,
                "strategy": "ml-powered"
            }
    except Exception as e:
        logger.warning(f"ML rate limit error: {e}")
    
    return {"allowed": True, "remaining": 1000, "limit": 1000, "strategy": "fallback"}

async def log_analytics(event_data: Dict[str, Any]):
    try:
        if http_client:
            await http_client.post(
                f"{ANALYTICS_SERVICE_URL}/events",
                json=event_data,
                timeout=1.0
            )
    except Exception as e:
        logger.warning(f"Analytics logging error: {e}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": VERSION,
        "features": ["ml_rate_limiting", "behavior_prediction"],
        "experimental": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    checks = {
        "redis": False,
        "http_client": http_client is not None
    }
    
    try:
        if redis_client:
            await redis_client.ping()
            checks["redis"] = True
    except:
        pass
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ready else "not_ready",
            "version": VERSION,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/api/v1/status")
async def get_status(
    x_user_id: Optional[str] = Header(None),
    x_tier: Optional[str] = Header("free")
):
    user_id = x_user_id or "anonymous"
    rate_limit = await ml_rate_limit_check(user_id, x_tier)
    
    if not rate_limit.get("allowed", True):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "ml_score": rate_limit.get("ml_score", 0),
                "strategy": "ml-powered"
            }
        )
    
    await log_analytics({
        "event": "status_check",
        "user_id": user_id,
        "tier": x_tier,
        "version": VERSION,
        "ml_score": rate_limit.get("ml_score", 0),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "status": "operational",
        "version": VERSION,
        "rate_limit_strategy": "ml-powered",
        "rate_limit_remaining": rate_limit.get("remaining", 0),
        "ml_score": rate_limit.get("ml_score", 0),
        "experimental": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/process")
async def process_request(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    x_tier: Optional[str] = Header("free")
):
    user_id = x_user_id or "anonymous"
    rate_limit = await ml_rate_limit_check(user_id, x_tier)
    
    if not rate_limit.get("allowed", True):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await request.json()
    except:
        body = {}
    
    # Advanced processing with optimization
    await asyncio.sleep(0.03)  # 30ms processing
    
    result = {
        "processed": True,
        "user_id": user_id,
        "tier": x_tier,
        "version": VERSION,
        "ml_powered": True,
        "ml_score": rate_limit.get("ml_score", 0),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await log_analytics({
        "event": "request_processed",
        "user_id": user_id,
        "tier": x_tier,
        "version": VERSION,
        "ml_score": rate_limit.get("ml_score", 0),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return result

@app.get("/api/v1/data/{item_id}")
async def get_data(
    item_id: str,
    x_user_id: Optional[str] = Header(None),
    x_tier: Optional[str] = Header("free")
):
    user_id = x_user_id or "anonymous"
    rate_limit = await ml_rate_limit_check(user_id, x_tier)
    
    if not rate_limit.get("allowed", True):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    await asyncio.sleep(0.02)
    
    data = {
        "id": item_id,
        "version": VERSION,
        "ml_powered": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return data

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
