from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import os
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Database Health Monitor")

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Configuration from environment
# NOTE: Default passwords are for demo/debugging scenarios only
# In production, always use environment variables and never hardcode passwords
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "debugdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "debuguser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "debugpass123")  # Demo password - use env var in production
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

class HealthCheck(BaseModel):
    service: str
    status: str
    latency_ms: float
    timestamp: datetime
    details: Optional[dict] = None

class StorageCheck(BaseModel):
    pvc_name: str
    namespace: str
    status: str
    capacity: str
    used: str

def get_postgres_connection():
    """Establish PostgreSQL connection with retry logic"""
    max_retries = 1  # Reduced retries for faster failure
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=2  # Reduced timeout to fail faster
            )
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"PostgreSQL connection attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)
            else:
                raise

def get_redis_connection():
    """Establish Redis connection"""
    return redis.Redis(host=REDIS_HOST, port=6379, db=0, socket_timeout=2, socket_connect_timeout=2)

@app.get("/")
async def root():
    return {
        "service": "Database Health Monitor",
        "version": "1.0.0",
        "purpose": "Monitor stateful application health for debugging scenarios"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Basic health check"""
    return HealthCheck(
        service="api",
        status="healthy",
        latency_ms=0.5,
        timestamp=datetime.utcnow()
    )

@app.get("/health/postgres", response_model=HealthCheck)
async def postgres_health():
    """Check PostgreSQL health and storage"""
    start_time = time.time()
    
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        # Check storage
        cursor.execute("""
            SELECT pg_database_size(current_database()) as db_size,
                   pg_size_pretty(pg_database_size(current_database())) as db_size_pretty;
        """)
        storage = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        latency = (time.time() - start_time) * 1000
        
        return HealthCheck(
            service="postgresql",
            status="healthy",
            latency_ms=round(latency, 2),
            timestamp=datetime.utcnow(),
            details={
                "version": version['version'],
                "database_size": storage['db_size_pretty'],
                "database_size_bytes": storage['db_size']
            }
        )
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        latency = (time.time() - start_time) * 1000
        
        # Provide user-friendly error message
        error_msg = str(e)
        if "name resolution" in error_msg.lower() or "could not translate host name" in error_msg.lower():
            error_msg = f"PostgreSQL service not found at '{POSTGRES_HOST}'. Service may not be deployed or hostname is incorrect."
        elif "timeout" in error_msg.lower():
            error_msg = f"Connection timeout to PostgreSQL at '{POSTGRES_HOST}'. Service may be unreachable."
        else:
            error_msg = f"PostgreSQL connection failed: {error_msg}"
        
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgresql",
                "status": "unhealthy",
                "error": error_msg,
                "latency_ms": round(latency, 2),
                "host": POSTGRES_HOST
            }
        )

@app.get("/health/redis", response_model=HealthCheck)
async def redis_health():
    """Check Redis health"""
    start_time = time.time()
    
    try:
        r = get_redis_connection()
        
        # Test operations
        r.ping()
        info = r.info()
        
        latency = (time.time() - start_time) * 1000
        
        return HealthCheck(
            service="redis",
            status="healthy",
            latency_ms=round(latency, 2),
            timestamp=datetime.utcnow(),
            details={
                "connected_clients": info.get('connected_clients'),
                "used_memory": info.get('used_memory_human'),
                "uptime_seconds": info.get('uptime_in_seconds')
            }
        )
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        latency = (time.time() - start_time) * 1000
        
        # Provide user-friendly error message
        error_msg = str(e)
        if "name resolution" in error_msg.lower() or "temporary failure" in error_msg.lower():
            error_msg = f"Redis service not found at '{REDIS_HOST}:6379'. Service may not be deployed or hostname is incorrect."
        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            error_msg = f"Connection timeout to Redis at '{REDIS_HOST}:6379'. Service may be unreachable."
        else:
            error_msg = f"Redis connection failed: {error_msg}"
        
        raise HTTPException(
            status_code=503,
            detail={
                "service": "redis",
                "status": "unhealthy",
                "error": error_msg,
                "latency_ms": round(latency, 2),
                "host": f"{REDIS_HOST}:6379"
            }
        )

@app.get("/health/all")
async def all_health_checks():
    """Check all services"""
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check PostgreSQL
    try:
        pg_result = await postgres_health()
        results["services"]["postgresql"] = pg_result.dict()
    except HTTPException as e:
        results["services"]["postgresql"] = e.detail
    
    # Check Redis
    try:
        redis_result = await redis_health()
        results["services"]["redis"] = redis_result.dict()
    except HTTPException as e:
        results["services"]["redis"] = e.detail
    
    # Overall status - more informative
    healthy_count = sum(1 for service in results["services"].values() if service.get("status") == "healthy")
    total_count = len(results["services"])
    
    if healthy_count == total_count and total_count > 0:
        results["overall_status"] = "healthy"
    elif healthy_count > 0:
        results["overall_status"] = "degraded"
        results["status_message"] = f"{healthy_count} of {total_count} services healthy"
    else:
        results["overall_status"] = "degraded"
        results["status_message"] = "All services unavailable. This is expected if databases are not deployed."
    
    return results

@app.post("/debug/simulate-load")
async def simulate_database_load(duration_seconds: int = 30):
    """Simulate database load for testing"""
    
    async def run_load_test():
        end_time = time.time() + duration_seconds
        operations = 0
        
        while time.time() < end_time:
            try:
                # PostgreSQL operations
                conn = get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT pg_sleep(0.1);")
                cursor.close()
                conn.close()
                
                # Redis operations
                r = get_redis_connection()
                r.set(f"load_test_{operations}", f"value_{operations}")
                r.get(f"load_test_{operations}")
                
                operations += 1
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Load test error: {e}")
    
    return {
        "message": f"Load test started for {duration_seconds} seconds",
        "note": "Check /health/all for service status"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
