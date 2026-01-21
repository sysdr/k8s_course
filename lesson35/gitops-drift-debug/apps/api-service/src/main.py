"""
API Service for GitOps Drift Detection Demo
Demonstrates production FastAPI patterns with observability
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import asyncio
import logging
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import redis.asyncio as redis
import json

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)
DRIFT_EVENTS = Counter(
    'drift_events_total',
    'Total drift events detected',
    ['resource_type', 'namespace']
)

# Models
class DriftEvent(BaseModel):
    """Model for drift detection events"""
    resource_type: str = Field(..., description="Kubernetes resource type")
    resource_name: str = Field(..., description="Resource name")
    namespace: str = Field(..., description="Kubernetes namespace")
    git_sha: str = Field(..., description="Git commit SHA")
    live_sha: str = Field(..., description="Live state SHA")
    user: Optional[str] = Field(None, description="User who made change")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # New fields for drift classification
    drift_type: Optional[str] = Field(None, description="Intentional, Accidental, or Malicious")
    drift_risk_level: Optional[str] = Field(None, description="Low, Medium, or High")
    change_description: Optional[str] = Field(None, description="Description of what changed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_type": "Deployment",
                "resource_name": "api-service",
                "namespace": "production",
                "git_sha": "abc123",
                "live_sha": "def456",
                "user": "john.doe@company.com",
                "timestamp": "2024-01-03T14:32:17Z"
            }
        }

class DeploymentInfo(BaseModel):
    """Current deployment information"""
    name: str
    namespace: str
    replicas: int
    image: str
    status: str
    drift_detected: bool = False
    # New fields for enhanced visibility
    health_status: str = "Healthy"  # Health vs Sync distinction
    sync_status: str = "Synced"  # Health vs Sync distinction
    sync_mode: str = "Manual"  # Auto vs Manual vs Delay
    auto_heal_enabled: bool = False
    drift_grace_window_minutes: Optional[int] = None  # Countdown timer
    drift_type: Optional[str] = None  # Intentional vs Accidental vs Malicious
    drift_risk_level: Optional[str] = None  # Low, Medium, High
    last_action_taken: Optional[str] = None  # Reconciliation outcome tracking
    last_action_timestamp: Optional[datetime] = None

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    dependencies: dict

# Application
app = FastAPI(
    title="GitOps Drift Detection API",
    description="Production API for demonstrating ArgoCD drift detection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection pool
redis_client: Optional[redis.Redis] = None

async def get_redis():
    """Dependency for Redis connection"""
    global redis_client
    if redis_client is None:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_client = await redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
    return redis_client

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("API Service starting up...")
    try:
        await get_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("API Service shutting down...")
    global redis_client
    if redis_client:
        await redis_client.close()

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint for Kubernetes probes
    Returns service health and dependency status
    """
    redis_status = "healthy"
    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        dependencies={
            "redis": redis_status
        }
    )

@app.get("/ready")
async def readiness_check():
    """
    Readiness probe - service is ready to accept traffic
    """
    try:
        r = await get_redis()
        await r.ping()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/api/v1/drift-events", response_model=List[DriftEvent])
async def get_drift_events(
    namespace: Optional[str] = None,
    limit: int = 100
):
    """
    Retrieve drift events from Redis
    
    This endpoint demonstrates how production systems track GitOps drift
    """
    REQUEST_COUNT.labels(method="GET", endpoint="/drift-events", status="200").inc()
    
    try:
        r = await get_redis()
        
        # Get drift events from Redis sorted set
        events_key = f"drift:events:{namespace}" if namespace else "drift:events:all"
        event_ids = await r.zrange(events_key, 0, limit - 1, desc=True)
        
        events = []
        for event_id in event_ids:
            event_data = await r.get(f"drift:event:{event_id}")
            if event_data:
                events.append(DriftEvent(**json.loads(event_data)))
        
        return events
    except Exception as e:
        logger.error(f"Error retrieving drift events: {e}")
        REQUEST_COUNT.labels(method="GET", endpoint="/drift-events", status="500").inc()
        raise HTTPException(status_code=500, detail="Failed to retrieve drift events")

@app.post("/api/v1/drift-events", response_model=DriftEvent, status_code=201)
async def create_drift_event(event: DriftEvent):
    """
    Record a new drift event
    
    This endpoint is called by the drift detection system when
    manual kubectl changes are detected
    """
    REQUEST_COUNT.labels(method="POST", endpoint="/drift-events", status="201").inc()
    DRIFT_EVENTS.labels(
        resource_type=event.resource_type,
        namespace=event.namespace
    ).inc()
    
    try:
        r = await get_redis()
        
        # Generate event ID
        event_id = f"{event.namespace}:{event.resource_name}:{int(event.timestamp.timestamp())}"
        
        # Store event data
        await r.set(
            f"drift:event:{event_id}",
            event.model_dump_json(),
            ex=86400 * 7  # Keep for 7 days
        )
        
        # Add to sorted sets for querying
        await r.zadd(
            f"drift:events:{event.namespace}",
            {event_id: event.timestamp.timestamp()}
        )
        await r.zadd(
            "drift:events:all",
            {event_id: event.timestamp.timestamp()}
        )
        
        logger.info(f"Drift event recorded: {event_id}")
        return event
    except Exception as e:
        logger.error(f"Error creating drift event: {e}")
        REQUEST_COUNT.labels(method="POST", endpoint="/drift-events", status="500").inc()
        raise HTTPException(status_code=500, detail="Failed to create drift event")

@app.get("/api/v1/deployments", response_model=List[DeploymentInfo])
async def get_deployments():
    """
    Get current deployment information
    
    This demonstrates how to track deployment state across environments
    """
    REQUEST_COUNT.labels(method="GET", endpoint="/deployments", status="200").inc()
    
    # Simulated deployment data with enhanced information
    # In production, this would query Kubernetes API and ArgoCD API
    deployments = [
        DeploymentInfo(
            name="api-service",
            namespace="production",
            replicas=3,
            image="api-service:v1.2.0",
            status="Healthy",
            drift_detected=False,
            health_status="Healthy",
            sync_status="Synced",
            sync_mode="Auto",
            auto_heal_enabled=True,
            drift_grace_window_minutes=None,
            drift_type=None,
            drift_risk_level=None,
            last_action_taken="Git updated and synced",
            last_action_timestamp=datetime.utcnow()
        ),
        DeploymentInfo(
            name="frontend",
            namespace="production",
            replicas=5,
            image="frontend:v2.1.0",
            status="Healthy",
            drift_detected=False,
            health_status="Healthy",
            sync_status="Synced",
            sync_mode="Auto",
            auto_heal_enabled=True,
            drift_grace_window_minutes=None,
            drift_type=None,
            drift_risk_level=None,
            last_action_taken="Git updated and synced",
            last_action_timestamp=datetime.utcnow()
        ),
        DeploymentInfo(
            name="worker",
            namespace="production",
            replicas=8,
            image="worker:v1.5.0",
            status="Degraded",
            drift_detected=True,  # Intentional drift for debugging
            health_status="Healthy",  # Pods are running fine
            sync_status="OutOfSync",  # But not synced with Git
            sync_mode="Manual",
            auto_heal_enabled=False,
            drift_grace_window_minutes=25,  # 25 minutes remaining in 30-min window
            drift_type="Intentional",
            drift_risk_level="Medium",
            last_action_taken="Manual kubectl scale (pending resolution)",
            last_action_timestamp=datetime.utcnow()
        )
    ]
    
    return deployments

@app.get("/api/v1/sync-status/{app_name}")
async def get_sync_status(app_name: str):
    """
    Get ArgoCD sync status for an application
    
    In production, this would query ArgoCD API
    """
    REQUEST_COUNT.labels(method="GET", endpoint="/sync-status", status="200").inc()
    
    # Simulated sync status with enhanced information
    # The worker app has intentional drift for debugging exercise
    status_map = {
        "api-service": {
            "sync_status": "Synced",
            "health_status": "Healthy",
            "git_sha": "abc123def",
            "live_sha": "abc123def",
            "drift_detected": False,
            "sync_mode": "Auto",
            "auto_heal_enabled": True,
            "drift_grace_window_minutes": None
        },
        "frontend": {
            "sync_status": "Synced",
            "health_status": "Healthy",
            "git_sha": "456ghi789",
            "live_sha": "456ghi789",
            "drift_detected": False,
            "sync_mode": "Auto",
            "auto_heal_enabled": True,
            "drift_grace_window_minutes": None
        },
        "worker": {
            "sync_status": "OutOfSync",
            "health_status": "Healthy",  # Pods are healthy, but out of sync
            "git_sha": "c0ffee000",
            "live_sha": "deadbeef0",
            "drift_detected": True,
            "sync_mode": "Manual",
            "auto_heal_enabled": False,
            "drift_grace_window_minutes": 25,  # 30-minute window, 5 minutes elapsed
            "drift_details": {
                "replicas": {"git": 2, "live": 8},
                "memory_limit": {"git": "512Mi", "live": "1Gi"}
            },
            "drift_type": "Intentional",
            "drift_risk_level": "Medium",
            "last_action_taken": "Manual kubectl scale",
            "last_action_timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        }
    }
    
    if app_name not in status_map:
        raise HTTPException(status_code=404, detail=f"Application {app_name} not found")
    
    return status_map[app_name]

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "GitOps Drift Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
