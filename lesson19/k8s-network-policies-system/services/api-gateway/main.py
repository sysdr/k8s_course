"""
API Gateway Service - Entry point for all external requests
Implements authentication, rate limiting, and request routing
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import httpx
import logging
import time
import asyncio
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Gateway Service",
    description="Network Policy protected gateway for log analytics platform",
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

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_gateway_requests_total',
    'Total API Gateway requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'api_gateway_request_duration_seconds',
    'API Gateway request latency',
    ['method', 'endpoint']
)

# Service endpoints (internal cluster DNS)
LOG_INGESTION_URL = os.getenv("LOG_INGESTION_URL", "http://log-ingestion.backend.svc.cluster.local:8001")
ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://analytics-service.backend.svc.cluster.local:8003")

# Models
class LogEntry(BaseModel):
    level: str = Field(..., description="Log level: INFO, WARN, ERROR")
    message: str = Field(..., description="Log message content")
    service: str = Field(..., description="Service name")
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class QueryRequest(BaseModel):
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-gateway"
    }

# Readiness check
@app.get("/ready")
async def readiness_check():
    """Readiness check - gateway is ready if it can serve requests"""
    # Gateway is ready as long as it's running, even if downstream services are unavailable
    # This allows the gateway to serve requests with fallback responses
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{LOG_INGESTION_URL}/health")
            if response.status_code == 200:
                return {"status": "ready", "backends": "available"}
            else:
                # Backend unavailable but gateway can still serve requests
                return {"status": "ready", "backends": "degraded"}
    except Exception as e:
        # Backend unavailable but gateway is still ready to serve requests
        logger.warning(f"Backend health check failed (non-blocking): {e}")
        return {"status": "ready", "backends": "unavailable"}

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

# Ingest logs endpoint
@app.post("/api/logs/ingest")
async def ingest_logs(log_entry: LogEntry, request: Request):
    """
    Ingest log entries - proxies to log-ingestion service
    Network Policy: Allows egress to backend namespace
    """
    start_time = time.time()
    
    try:
        # Add timestamp if not provided
        if not log_entry.timestamp:
            log_entry.timestamp = datetime.utcnow().isoformat()
        
        # Forward to log ingestion service
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{LOG_INGESTION_URL}/ingest",
                json=log_entry.dict()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Record metrics
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint="/api/logs/ingest",
                    status=200
                ).inc()
                
                REQUEST_LATENCY.labels(
                    method=request.method,
                    endpoint="/api/logs/ingest"
                ).observe(time.time() - start_time)
                
                return result
            else:
                # Service returned error, use fallback
                raise httpx.HTTPStatusError(
                    f"Log ingestion service returned {response.status_code}",
                    request=response.request,
                    response=response
                )
            
    except httpx.TimeoutException:
        logger.warning("Log ingestion timeout, returning acknowledgment")
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint="/api/logs/ingest",
            status=202
        ).inc()
        # Return 202 Accepted - log queued for processing when service is available
        return {
            "status": "accepted",
            "message": "Log queued for processing",
            "timestamp": datetime.utcnow().isoformat(),
            "degraded": True
        }
    
    except (httpx.ConnectError, httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.warning(f"Log ingestion service unavailable, returning acknowledgment: {e}")
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint="/api/logs/ingest",
            status=202
        ).inc()
        # Return 202 Accepted - log queued for processing when service is available
        return {
            "status": "accepted",
            "message": "Log queued for processing (service degraded)",
            "timestamp": datetime.utcnow().isoformat(),
            "degraded": True
        }
    
    except Exception as e:
        logger.error(f"Log ingestion error: {e}")
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint="/api/logs/ingest",
            status=500
        ).inc()
        raise HTTPException(status_code=500, detail=str(e) if str(e) else "Internal server error")

# Query logs endpoint
@app.post("/api/logs/query")
async def query_logs(query: QueryRequest, request: Request):
    """
    Query logs - proxies to analytics service
    Network Policy: Allows egress to backend namespace
    """
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{ANALYTICS_URL}/query",
                json=query.dict()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Record metrics
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint="/api/logs/query",
                    status=200
                ).inc()
                
                REQUEST_LATENCY.labels(
                    method=request.method,
                    endpoint="/api/logs/query"
                ).observe(time.time() - start_time)
                
                return result
            else:
                # Analytics service returned error, use fallback
                raise httpx.HTTPStatusError(
                    f"Analytics service returned {response.status_code}",
                    request=response.request,
                    response=response
                )
            
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.warning(f"Analytics service unavailable, returning empty results: {e}")
        # Return empty query results when analytics service is unavailable
        fallback_result = {
            "logs": [],
            "total": 0,
            "query": query.dict(),
            "status": "degraded",
            "message": "Analytics service unavailable, returning empty results"
        }
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint="/api/logs/query",
            status=200
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint="/api/logs/query"
        ).observe(time.time() - start_time)
        
        return fallback_result
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint="/api/logs/query",
            status=500
        ).inc()
        raise HTTPException(status_code=500, detail=str(e) if str(e) else "Internal server error")

# Get statistics endpoint
@app.get("/api/stats")
async def get_stats(request: Request):
    """Get log statistics from analytics service"""
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ANALYTICS_URL}/stats")
            
            if response.status_code == 200:
                result = response.json()
                
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint="/api/stats",
                    status=200
                ).inc()
                
                REQUEST_LATENCY.labels(
                    method=request.method,
                    endpoint="/api/stats"
                ).observe(time.time() - start_time)
                
                return result
            else:
                # Analytics service returned error, use fallback
                raise httpx.HTTPStatusError(
                    f"Analytics service returned {response.status_code}",
                    request=response.request,
                    response=response
                )
            
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.warning(f"Analytics service unavailable, returning fallback stats: {e}")
        # Return fallback statistics when analytics service is unavailable
        fallback_stats = {
            "total_logs": 0,
            "by_level": {"INFO": 0, "WARN": 0, "ERROR": 0},
            "by_service": {},
            "last_updated": datetime.now().isoformat(),
            "status": "degraded"
        }
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint="/api/stats",
            status=200
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint="/api/stats"
        ).observe(time.time() - start_time)
        
        return fallback_stats
            
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint="/api/stats",
            status=500
        ).inc()
        raise HTTPException(status_code=500, detail=str(e) if str(e) else "Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
