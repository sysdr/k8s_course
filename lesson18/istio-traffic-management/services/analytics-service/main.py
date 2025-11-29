"""
Analytics Service - Event collection and aggregation
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY, CollectorRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clear any existing metrics in the registry to avoid duplicates
# This can happen if the module is reloaded
try:
    # Get all collectors and unregister them
    collectors_to_remove = list(REGISTRY._collector_to_names.keys())
    for collector in collectors_to_remove:
        try:
            REGISTRY.unregister(collector)
        except (KeyError, ValueError, AttributeError):
            pass
except (AttributeError, KeyError, TypeError):
    # If registry structure is different, try to create a new registry
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

# Metrics - wrap in try-except to handle any import-time errors
try:
    EVENTS_RECEIVED = safe_metric(
        Counter, 'analytics_events_received_total',
        'Total events received',
        ['event_type', 'version']
    )
except Exception as e:
    logger.warning(f"Failed to create EVENTS_RECEIVED metric: {e}")
    class DummyMetric:
        def labels(self, **kwargs): return self
        def inc(self, value=1): pass
        def observe(self, value): pass
    EVENTS_RECEIVED = DummyMetric()

try:
    EVENT_PROCESSING_DURATION = safe_metric(
        Histogram, 'analytics_event_processing_seconds',
        'Event processing duration'
    )
except Exception as e:
    logger.warning(f"Failed to create EVENT_PROCESSING_DURATION metric: {e}")
    class DummyMetric:
        def labels(self, **kwargs): return self
        def inc(self, value=1): pass
        def observe(self, value): pass
    EVENT_PROCESSING_DURATION = DummyMetric()

# In-memory storage (use database in production)
events_store: List[Dict[str, Any]] = []

class AnalyticsEvent(BaseModel):
    event: str
    user_id: str
    tier: str
    version: str
    timestamp: str
    ml_score: float = 0.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Analytics Service")
    yield
    logger.info("Shutting down Analytics Service")

app = FastAPI(title="Analytics Service", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "service": "analytics"}

@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/events")
async def log_event(event: AnalyticsEvent):
    """Log analytics event"""
    EVENTS_RECEIVED.labels(
        event_type=event.event,
        version=event.version
    ).inc()
    
    events_store.append(event.dict())
    
    # Keep only last 10000 events in memory
    if len(events_store) > 10000:
        events_store.pop(0)
    
    return {"status": "logged", "event_id": len(events_store)}

@app.get("/events")
async def get_events(limit: int = 100, event_type: str = None):
    """Get recent events"""
    filtered = events_store
    if event_type:
        filtered = [e for e in events_store if e.get("event") == event_type]
    return {"events": filtered[-limit:], "total": len(filtered)}

@app.get("/stats")
async def get_stats():
    """Get aggregated statistics"""
    if not events_store:
        return {"total_events": 0}
    
    stats = {
        "total_events": len(events_store),
        "by_version": {},
        "by_event_type": {},
        "by_tier": {}
    }
    
    for event in events_store:
        version = event.get("version", "unknown")
        event_type = event.get("event", "unknown")
        tier = event.get("tier", "unknown")
        
        stats["by_version"][version] = stats["by_version"].get(version, 0) + 1
        stats["by_event_type"][event_type] = stats["by_event_type"].get(event_type, 0) + 1
        stats["by_tier"][tier] = stats["by_tier"].get(tier, 0) + 1
    
    return stats

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info")
