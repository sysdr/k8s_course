"""
API Gateway Service - Entry point for all client requests
Implements rate limiting, authentication, and request routing
"""
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
import time
from datetime import datetime
import logging
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_gateway_request_duration_seconds', 'Request duration', ['endpoint'])
SECURITY_EVENTS = Counter('api_gateway_security_events_total', 'Security events', ['event_type'])

app = FastAPI(
    title="Secure API Gateway",
    description="DevSecOps API Gateway with security controls",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service endpoints
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
LOG_PROCESSOR_URL = os.getenv("LOG_PROCESSOR_URL", "http://log-processor:8002")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8003")
SECURITY_SERVICE_URL = os.getenv("SECURITY_SERVICE_URL", "http://security-service:8004")

# Rate limiting (simple in-memory, use Redis in production)
rate_limit_store: Dict[str, list] = {}
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    dependencies: Dict[str, str]

class LogEntry(BaseModel):
    level: str
    message: str
    service: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuthRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limiting implementation"""
    now = time.time()
    
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    
    # Clean old entries
    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip]
        if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT:
        SECURITY_EVENTS.labels(event_type='rate_limit_exceeded').inc()
        return False
    
    rate_limit_store[client_ip].append(now)
    return True

def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

async def verify_token(request: Request) -> Dict[str, Any]:
    """Verify JWT token with auth service"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        SECURITY_EVENTS.labels(event_type='missing_token').inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/verify",
                json={"token": token},
                timeout=5.0
            )
            
            if response.status_code != 200:
                SECURITY_EVENTS.labels(event_type='invalid_token').inc()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Auth service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Apply security controls to all requests"""
    start_time = time.time()
    
    # Check rate limit
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(endpoint=request.url.path).observe(duration)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kubernetes health check endpoint"""
    dependencies = {}
    
    # Check auth service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AUTH_SERVICE_URL}/health", timeout=2.0)
            dependencies["auth_service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        dependencies["auth_service"] = "unavailable"
    
    # Check log processor
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LOG_PROCESSOR_URL}/health", timeout=2.0)
            dependencies["log_processor"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        dependencies["log_processor"] = "unavailable"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        dependencies=dependencies
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/auth/login", response_model=TokenResponse)
async def login(auth_req: AuthRequest):
    """Authenticate user and return JWT token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/login",
                json=auth_req.dict(),
                timeout=5.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Auth service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

@app.post("/logs", dependencies=[Depends(verify_token)])
async def submit_log(log_entry: LogEntry):
    """Submit log entry for processing"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LOG_PROCESSOR_URL}/logs",
                json=log_entry.dict(),
                timeout=5.0
            )
            
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Log processor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Log processor unavailable"
        )

@app.get("/analytics/summary", dependencies=[Depends(verify_token)])
async def get_analytics_summary(time_range: str = "1h"):
    """Get analytics summary from analytics service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ANALYTICS_SERVICE_URL}/summary",
                params={"time_range": time_range},
                timeout=10.0
            )
            
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Analytics service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service unavailable"
        )

@app.get("/security/dashboard", dependencies=[Depends(verify_token)])
async def get_security_dashboard():
    """Get complete security dashboard data"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/dashboard",
                timeout=10.0
            )
            
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Security service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )

@app.get("/security/vulnerabilities", dependencies=[Depends(verify_token)])
async def get_vulnerabilities():
    """Get vulnerability scanning results"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/vulnerabilities",
                timeout=10.0
            )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Security service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )

@app.get("/security/policy-violations", dependencies=[Depends(verify_token)])
async def get_policy_violations():
    """Get policy violation summary"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/policy-violations",
                timeout=10.0
            )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Security service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )

@app.get("/security/runtime-threats", dependencies=[Depends(verify_token)])
async def get_runtime_threats():
    """Get runtime threat detection summary"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/runtime-threats",
                timeout=10.0
            )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Security service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )

@app.get("/security/network", dependencies=[Depends(verify_token)])
async def get_network_security():
    """Get network security metrics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/network-security",
                timeout=10.0
            )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Security service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )

@app.get("/security/secrets", dependencies=[Depends(verify_token)])
async def get_secrets_activity():
    """Get secrets management activity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/secrets",
                timeout=10.0
            )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Security service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )

@app.get("/security/audit", dependencies=[Depends(verify_token)])
async def get_audit_logs():
    """Get audit and compliance logs"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/audit",
                timeout=10.0
            )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Security service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
