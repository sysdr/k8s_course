"""
API Gateway v2 - Canary Version with Enhanced Caching
Improved cache strategy with predictive prefetching
"""
import asyncio
import logging
import os
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header, Depends
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

# Prometheus metrics - safely register
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
CACHE_HITS = safe_metric(
    Counter, 'api_gateway_cache_hits_total',
    'Cache hits',
    ['version']
)
CACHE_MISSES = safe_metric(
    Counter, 'api_gateway_cache_misses_total',
    'Cache misses',
    ['version']
)
CACHE_PREFETCH = safe_metric(
    Counter, 'api_gateway_cache_prefetch_total',
    'Cache prefetch operations',
    ['version']
)

VERSION = "v2"
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8080")
RATE_LIMITER_URL = os.getenv("RATE_LIMITER_URL", "http://rate-limiter:8080")

redis_client: Optional[redis.Redis] = None
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, http_client
    
    logger.info(f"Starting API Gateway {VERSION} with enhanced caching")
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
    
    # Start cache warming background task
    asyncio.create_task(cache_warming_task())
    
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
        response.headers["X-Cache-Strategy"] = "enhanced"
        
        return response
    finally:
        ACTIVE_CONNECTIONS.labels(version=VERSION).dec()

async def cache_warming_task():
    """Background task to warm cache with frequently accessed data"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            if redis_client:
                # Get most accessed items from analytics
                # In production, this would query analytics service
                popular_items = ["item-1", "item-2", "item-3"]
                for item_id in popular_items:
                    cache_key = f"data:{item_id}"
                    exists = await redis_client.exists(cache_key)
                    if not exists:
                        # Prefetch data
                        data = {
                            "id": item_id,
                            "version": VERSION,
                            "prefetched": True,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await redis_client.setex(cache_key, 300, json.dumps(data))
                        CACHE_PREFETCH.labels(version=VERSION).inc()
                        logger.info(f"Prefetched data for {item_id}")
        except Exception as e:
            logger.warning(f"Cache warming error: {e}")

async def check_rate_limit(user_id: str, tier: str = "free") -> Dict[str, Any]:
    try:
        if not http_client:
            return {"allowed": True, "remaining": 1000}
        response = await http_client.post(
            f"{RATE_LIMITER_URL}/check",
            json={"user_id": user_id, "tier": tier},
            timeout=2.0
        )
        return response.json()
    except Exception as e:
        logger.warning(f"Rate limiter error: {e}")
        return {"allowed": True, "remaining": 1000}

async def get_from_cache(key: str) -> Optional[str]:
    try:
        if not redis_client:
            return None
        value = await redis_client.get(key)
        if value:
            CACHE_HITS.labels(version=VERSION).inc()
            # Extend TTL on hit (LRU strategy)
            await redis_client.expire(key, 300)
        else:
            CACHE_MISSES.labels(version=VERSION).inc()
        return value
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
        CACHE_MISSES.labels(version=VERSION).inc()
        return None

async def set_cache(key: str, value: str, ttl: int = 300):
    try:
        if redis_client:
            await redis_client.setex(key, ttl, value)
    except Exception as e:
        logger.warning(f"Cache set error: {e}")

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
        "features": ["enhanced_caching", "cache_warming"],
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
    rate_limit = await check_rate_limit(user_id, x_tier)
    
    if not rate_limit.get("allowed", True):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    await log_analytics({
        "event": "status_check",
        "user_id": user_id,
        "tier": x_tier,
        "version": VERSION,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Get cache stats
    cache_stats = {}
    try:
        if redis_client:
            info = await redis_client.info("stats")
            cache_stats = {
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
    except:
        pass
    
    return {
        "status": "operational",
        "version": VERSION,
        "cache_enabled": redis_client is not None,
        "cache_strategy": "enhanced_with_warming",
        "cache_stats": cache_stats,
        "rate_limit_remaining": rate_limit.get("remaining", 0),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/process")
async def process_request(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    x_tier: Optional[str] = Header("free")
):
    user_id = x_user_id or "anonymous"
    rate_limit = await check_rate_limit(user_id, x_tier)
    
    if not rate_limit.get("allowed", True):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await request.json()
    except:
        body = {}
    
    cache_key = f"process:{user_id}:{hash(str(body))}"
    cached = await get_from_cache(cache_key)
    if cached:
        return JSONResponse(content={
            "cached": True,
            "result": cached,
            "version": VERSION,
            "cache_strategy": "enhanced"
        })
    
    # Improved processing (slightly faster)
    await asyncio.sleep(0.04)  # 40ms vs 50ms in v1
    
    result = {
        "processed": True,
        "user_id": user_id,
        "tier": x_tier,
        "version": VERSION,
        "optimized": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await set_cache(cache_key, json.dumps(result), ttl=60)
    
    await log_analytics({
        "event": "request_processed",
        "user_id": user_id,
        "tier": x_tier,
        "version": VERSION,
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
    rate_limit = await check_rate_limit(user_id, x_tier)
    
    if not rate_limit.get("allowed", True):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    cache_key = f"data:{item_id}"
    cached = await get_from_cache(cache_key)
    if cached:
        return JSONResponse(content={
            "cached": True,
            "data": json.loads(cached),
            "version": VERSION,
            "cache_strategy": "enhanced"
        })
    
    await asyncio.sleep(0.025)  # Faster data retrieval
    
    data = {
        "id": item_id,
        "version": VERSION,
        "optimized": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await set_cache(cache_key, json.dumps(data), ttl=300)
    
    return data

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
