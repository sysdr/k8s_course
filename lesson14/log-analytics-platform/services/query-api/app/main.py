from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import asyncpg
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Query API Service", version="1.0.0")

# Prometheus metrics
query_counter = Counter('queries_executed_total', 'Total queries executed', ['query_type'])
query_duration = Histogram('query_duration_seconds', 'Query execution time')
query_errors = Counter('query_errors_total', 'Total query errors')

# Database connection pool
db_pool = None

class LogQueryRequest(BaseModel):
    start_time: Optional[datetime] = Field(default_factory=lambda: datetime.utcnow() - timedelta(hours=1))
    end_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    level: Optional[str] = None
    source: Optional[str] = None
    limit: int = Field(default=100, le=1000)

class LogQueryResponse(BaseModel):
    logs: List[dict]
    total_count: int
    query_time_ms: float

class AggregationRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    group_by: str = Field(..., description="Field to group by: level, source, or host")
    interval: str = Field(default="1h", description="Time interval: 1m, 5m, 1h, 1d")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_host = os.getenv("DB_HOST", "timescaledb-lb.log-analytics.svc.cluster.local")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME", "logs")
        
        if not db_user or not db_password:
            raise ValueError("DB_USER and DB_PASSWORD environment variables must be set")
        
        db_pool = await asyncpg.create_pool(
            host=db_host,
            port=5432,
            user=db_user,
            password=db_password,
            database=db_name,
            min_size=5,
            max_size=20
        )
        
        # Create table if not exists
        async with db_pool.acquire() as conn:
            # Check if table exists and if it's already a hypertable
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'logs'
                )
            """)
            
            if not table_exists:
                # Create table without PRIMARY KEY (TimescaleDB requirement for hypertables)
                await conn.execute('''
                    CREATE TABLE logs (
                        id SERIAL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        level VARCHAR(10) NOT NULL,
                        message TEXT NOT NULL,
                        source VARCHAR(255) NOT NULL,
                        host VARCHAR(255),
                        metadata JSONB,
                        PRIMARY KEY (id, timestamp)
                    );
                ''')
                
                # Convert to hypertable
                await conn.execute("SELECT create_hypertable('logs', 'timestamp', if_not_exists => TRUE);")
                
                # Create indexes
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp DESC);')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs (level);')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_source ON logs (source);')
            else:
                # Table exists, just ensure indexes exist
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp DESC);')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs (level);')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_source ON logs (source);')
        
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool"""
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "query-api"}

@app.get("/ready")
async def readiness_check():
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database check failed: {str(e)}")

@app.post("/query")
async def query_logs(request: LogQueryRequest) -> LogQueryResponse:
    """Query logs with filters"""
    try:
        query_counter.labels(query_type="search").inc()
        
        # Build dynamic query
        conditions = ["timestamp >= $1", "timestamp <= $2"]
        params = [request.start_time, request.end_time]
        param_count = 2
        
        if request.level:
            param_count += 1
            conditions.append(f"level = ${param_count}")
            params.append(request.level)
        
        if request.source:
            param_count += 1
            conditions.append(f"source = ${param_count}")
            params.append(request.source)
        
        where_clause = " AND ".join(conditions)
        
        start = datetime.utcnow()
        
        async with db_pool.acquire() as conn:
            # Get total count
            count_query = f"SELECT COUNT(*) FROM logs WHERE {where_clause}"
            total_count = await conn.fetchval(count_query, *params)
            
            # Get logs
            logs_query = f"""
                SELECT id, timestamp, level, message, source, host, metadata
                FROM logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${param_count + 1}
            """
            params.append(request.limit)
            
            rows = await conn.fetch(logs_query, *params)
            logs = [dict(row) for row in rows]
        
        query_time = (datetime.utcnow() - start).total_seconds()
        query_duration.observe(query_time)
        
        return LogQueryResponse(
            logs=logs,
            total_count=total_count,
            query_time_ms=query_time * 1000
        )
    except Exception as e:
        query_errors.inc()
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/aggregate")
async def aggregate_logs(request: AggregationRequest):
    """Aggregate logs by time bucket and field"""
    start = datetime.utcnow()
    try:
        query_counter.labels(query_type="aggregate").inc()
        
        interval_map = {
            "1m": "1 minute",
            "5m": "5 minutes",
            "15m": "15 minutes",
            "1h": "1 hour",
            "1d": "1 day"
        }
        
        if request.interval not in interval_map:
            raise HTTPException(status_code=400, detail="Invalid interval")
        
        bucket_interval = interval_map[request.interval]
        
        query = f"""
            SELECT
                time_bucket($1::interval, timestamp) AS bucket,
                {request.group_by},
                COUNT(*) as count
            FROM logs
            WHERE timestamp >= $2 AND timestamp <= $3
            GROUP BY bucket, {request.group_by}
            ORDER BY bucket DESC
        """
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, bucket_interval, request.start_time, request.end_time)
            results = [dict(row) for row in rows]
        
        query_time = (datetime.utcnow() - start).total_seconds()
        query_duration.observe(query_time)
        
        return {
            "aggregations": results,
            "interval": request.interval,
            "group_by": request.group_by
        }
    except Exception as e:
        query_errors.inc()
        logger.error(f"Aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        async with db_pool.acquire() as conn:
            total_logs = await conn.fetchval("SELECT COUNT(*) FROM logs")
            oldest_log = await conn.fetchval("SELECT MIN(timestamp) FROM logs")
            newest_log = await conn.fetchval("SELECT MAX(timestamp) FROM logs")
        
        return {
            "total_logs": total_logs,
            "oldest_log": oldest_log,
            "newest_log": newest_log,
            "database": "timescaledb"
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
