"""
API Gateway - Central routing and authentication service
Handles all external requests and routes to internal microservices
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import logging
import time
from datetime import datetime
import os
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service discovery using Kubernetes DNS
SERVICE_ENDPOINTS = {
    "log_ingestion": os.getenv("LOG_INGESTION_URL", "http://log-ingestion:8080"),
    "log_processor": os.getenv("LOG_PROCESSOR_URL", "http://log-processor:8080"),
    "query_service": os.getenv("QUERY_SERVICE_URL", "http://query-service:8080"),
}

# Connection pool configuration
client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
    limits=httpx.Limits(max_keepalive_connections=100, max_connections=200)
)

# Request/Response Models
class LogEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = Field(..., description="Log level: INFO, WARN, ERROR")
    service: str = Field(..., description="Source service name")
    message: str = Field(..., description="Log message")
    metadata: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = Field(default=100, le=1000)

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    dependencies: Dict[str, str]

# Middleware for request logging and metrics
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} Duration: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "logs": "/api/v1/logs",
            "query": "/api/v1/query",
            "stats": "/api/v1/stats"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint with dependency status
    Kubernetes uses this for readiness probes
    """
    dependencies = {}
    
    # Check all downstream services
    for service_name, endpoint in SERVICE_ENDPOINTS.items():
        try:
            response = await client.get(f"{endpoint}/health", timeout=5.0)
            dependencies[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            dependencies[service_name] = f"unhealthy: {str(e)}"
            logger.error(f"Health check failed for {service_name}: {e}")
    
    # Service is healthy if at least ingestion service is available
    overall_status = "healthy" if dependencies.get("log_ingestion") == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        service="api-gateway",
        timestamp=datetime.utcnow().isoformat(),
        dependencies=dependencies
    )

@app.post("/api/v1/logs", status_code=201)
async def ingest_logs(log_entry: LogEntry):
    """
    Ingest log entry - Routes to log-ingestion service via ClusterIP
    Demonstrates internal service discovery
    """
    try:
        response = await client.post(
            f"{SERVICE_ENDPOINTS['log_ingestion']}/ingest",
            json=log_entry.dict(),
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Log ingestion failed: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during log ingestion: {e}")
        raise HTTPException(status_code=500, detail="Internal service error")

@app.post("/api/v1/query")
async def query_logs(query: QueryRequest):
    """
    Query logs - Routes to query-service via ClusterIP
    Supports filtering by service, level, and time range
    """
    try:
        response = await client.post(
            f"{SERVICE_ENDPOINTS['query_service']}/query",
            json=query.dict(),
            timeout=15.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during query: {e}")
        raise HTTPException(status_code=500, detail="Internal service error")

@app.get("/api/v1/stats")
async def get_stats():
    """Get aggregated statistics from processor service"""
    try:
        response = await client.get(
            f"{SERVICE_ENDPOINTS['log_processor']}/stats",
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
        raise HTTPException(status_code=500, detail="Stats unavailable")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    # In production, use prometheus_client library
    metrics_text = """# HELP api_gateway_requests_total Total number of requests
# TYPE api_gateway_requests_total counter
api_gateway_requests_total{service="api-gateway"} 1000
# HELP api_gateway_request_duration_seconds Request duration in seconds
# TYPE api_gateway_request_duration_seconds histogram
api_gateway_request_duration_seconds{service="api-gateway",quantile="0.5"} 0.05
api_gateway_request_duration_seconds{service="api-gateway",quantile="0.99"} 0.1
# HELP api_gateway_active_connections Active connections
# TYPE api_gateway_active_connections gauge
api_gateway_active_connections{service="api-gateway"} 50
"""
    return Response(content=metrics_text, media_type="text/plain")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await client.aclose()
    logger.info("API Gateway shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
