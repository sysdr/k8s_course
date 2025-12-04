"""
Analytics Service - Query and analyze stored logs
Network Policy: Accepts traffic from API Gateway, connects to database
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from prometheus_client import Counter, Histogram, generate_latest
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Analytics Service",
    description="Query and analyze log data",
    version="1.0.0"
)

# Prometheus metrics
QUERY_COUNT = Counter(
    'analytics_queries_total',
    'Total analytics queries',
    ['query_type']
)
QUERY_LATENCY = Histogram(
    'analytics_query_duration_seconds',
    'Analytics query latency'
)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "timescaledb.data-layer.svc.cluster.local")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "logs")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

class QueryRequest(BaseModel):
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)

class LogRecord(BaseModel):
    id: int
    timestamp: str
    level: str
    service: str
    message: str
    metadata: Dict[str, Any]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "analytics"
    }

@app.get("/ready")
async def readiness_check():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(generate_latest(), media_type="text/plain")

@app.post("/query")
async def query_logs(query: QueryRequest):
    """
    Query logs with filters
    Network Policy: Only callable by api-gateway
    """
    start_time = time.time()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query
        sql = "SELECT * FROM logs WHERE 1=1"
        params = []
        
        if query.service:
            sql += " AND service = %s"
            params.append(query.service)
        
        if query.level:
            sql += " AND level = %s"
            params.append(query.level.upper())
        
        if query.start_time:
            sql += " AND timestamp >= %s"
            params.append(query.start_time)
        
        if query.end_time:
            sql += " AND timestamp <= %s"
            params.append(query.end_time)
        
        sql += " ORDER BY timestamp DESC LIMIT %s"
        params.append(query.limit)
        
        cur.execute(sql, params)
        results = cur.fetchall()
        
        # Convert to response format
        logs = []
        for row in results:
            logs.append({
                "id": row['id'],
                "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                "level": row['level'],
                "service": row['service'],
                "message": row['message'],
                "metadata": row['metadata'] or {}
            })
        
        cur.close()
        conn.close()
        
        # Record metrics
        QUERY_COUNT.labels(query_type='search').inc()
        QUERY_LATENCY.observe(time.time() - start_time)
        
        return {
            "status": "success",
            "count": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get log statistics"""
    start_time = time.time()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total count
        cur.execute("SELECT COUNT(*) as total FROM logs")
        total = cur.fetchone()['total']
        
        # Count by level
        cur.execute("""
            SELECT level, COUNT(*) as count
            FROM logs
            GROUP BY level
            ORDER BY count DESC
        """)
        by_level = {row['level']: row['count'] for row in cur.fetchall()}
        
        # Count by service
        cur.execute("""
            SELECT service, COUNT(*) as count
            FROM logs
            GROUP BY service
            ORDER BY count DESC
            LIMIT 10
        """)
        by_service = {row['service']: row['count'] for row in cur.fetchall()}
        
        # Recent activity (last hour)
        cur.execute("""
            SELECT COUNT(*) as count
            FROM logs
            WHERE timestamp > NOW() - INTERVAL '1 hour'
        """)
        recent = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        QUERY_COUNT.labels(query_type='stats').inc()
        QUERY_LATENCY.observe(time.time() - start_time)
        
        return {
            "total_logs": total,
            "by_level": by_level,
            "by_service": by_service,
            "last_hour": recent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
