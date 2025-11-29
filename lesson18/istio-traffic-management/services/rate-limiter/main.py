"""
Rate Limiter Service - Centralized rate limiting
"""
import logging
from datetime import datetime
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, generate_latest, REGISTRY

logging.basicConfig(level=logging.INFO)
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

RATE_LIMIT_CHECKS = safe_metric(
    Counter, 'rate_limiter_checks_total',
    'Total rate limit checks',
    ['tier', 'result']
)

# In-memory rate limits (use Redis in production)
rate_limits: Dict[str, Dict] = {}

class RateLimitRequest(BaseModel):
    user_id: str
    tier: str = "free"

TIER_LIMITS = {
    "free": 100,
    "premium": 1000,
    "enterprise": 10000
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Rate Limiter Service")
    yield
    logger.info("Shutting down Rate Limiter Service")

app = FastAPI(title="Rate Limiter Service", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rate-limiter"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "service": "rate-limiter"}

@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/check")
async def check_rate_limit(req: RateLimitRequest):
    """Check if user is within rate limits"""
    user_key = f"{req.user_id}:{req.tier}"
    limit = TIER_LIMITS.get(req.tier, 100)
    
    if user_key not in rate_limits:
        rate_limits[user_key] = {"count": 0, "reset_time": datetime.utcnow()}
    
    user_data = rate_limits[user_key]
    
    # Reset if hour has passed
    if (datetime.utcnow() - user_data["reset_time"]).seconds > 3600:
        user_data["count"] = 0
        user_data["reset_time"] = datetime.utcnow()
    
    user_data["count"] += 1
    remaining = max(0, limit - user_data["count"])
    allowed = remaining > 0
    
    RATE_LIMIT_CHECKS.labels(
        tier=req.tier,
        result="allowed" if allowed else "denied"
    ).inc()
    
    return {
        "allowed": allowed,
        "remaining": remaining,
        "limit": limit,
        "reset_time": user_data["reset_time"].isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info")
