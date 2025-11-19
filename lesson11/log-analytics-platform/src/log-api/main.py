import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

# Configuration
CONFIG = {
    "log_level": os.getenv("LOG_LEVEL", "info"),
    "db_host": os.getenv("DB_HOST", "postgres"),
    "db_port": os.getenv("DB_PORT", "5432"),
    "db_name": os.getenv("DB_NAME", "logs"),
    "db_user": os.getenv("DB_USER", "log_api"),
    "db_password": os.getenv("DB_PASSWORD", ""),
    "redis_host": os.getenv("REDIS_HOST", "redis"),
    "redis_password": os.getenv("REDIS_PASSWORD", ""),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
}

logging.basicConfig(
    level=getattr(logging, CONFIG["log_level"].upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
QUERIES = Counter('log_queries_total', 'Total log queries', ['endpoint'])
QUERY_DURATION = Histogram('query_duration_seconds', 'Query duration')

# Global clients
redis_client: Optional[redis.Redis] = None
db_engine = None

class LogResponse(BaseModel):
    id: int
    timestamp: datetime
    level: str
    service: str
    message: str
    metadata: dict
    trace_id: Optional[str]

class LogStats(BaseModel):
    total_logs: int
    logs_by_level: dict
    logs_by_service: dict
    time_range: dict

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, db_engine
    
    db_url = f"postgresql+asyncpg://{CONFIG['db_user']}:{CONFIG['db_password']}@{CONFIG['db_host']}:{CONFIG['db_port']}/{CONFIG['db_name']}"
    db_engine = create_async_engine(db_url, pool_size=20, max_overflow=40)
    
    redis_client = redis.Redis(
        host=CONFIG["redis_host"],
        password=CONFIG["redis_password"] or None,
        decode_responses=True
    )
    
    yield
    
    redis_client.close()
    await db_engine.dispose()

app = FastAPI(
    title="Log API Service",
    description="Query and analyze logs",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "log-api"}

@app.get("/ready")
async def readiness_check():
    try:
        redis_client.ping()
        async with db_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/logs", response_model=list[LogResponse])
async def query_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0
):
    QUERIES.labels(endpoint='logs').inc()
    
    with QUERY_DURATION.time():
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            query = "SELECT id, timestamp, level, service, message, metadata, trace_id FROM logs WHERE 1=1"
            params = {}
            
            if service:
                query += " AND service = :service"
                params["service"] = service
            if level:
                query += " AND level = :level"
                params["level"] = level
            if start_time:
                query += " AND timestamp >= :start_time"
                params["start_time"] = start_time
            if end_time:
                query += " AND timestamp <= :end_time"
                params["end_time"] = end_time
            
            query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            return [
                LogResponse(
                    id=row[0],
                    timestamp=row[1],
                    level=row[2],
                    service=row[3],
                    message=row[4],
                    metadata=json.loads(row[5]) if row[5] else {},
                    trace_id=row[6]
                )
                for row in rows
            ]

@app.get("/logs/recent/{service}")
async def get_recent_logs(service: str, limit: int = Query(default=100, le=1000)):
    QUERIES.labels(endpoint='recent').inc()
    
    # Try cache first
    cached = redis_client.zrevrange(f"recent_logs:{service}", 0, limit - 1)
    if cached:
        return [json.loads(log) for log in cached]
    
    # Fallback to database
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT id, timestamp, level, service, message, metadata, trace_id 
                FROM logs WHERE service = :service 
                ORDER BY timestamp DESC LIMIT :limit
            """),
            {"service": service, "limit": limit}
        )
        return [dict(row._mapping) for row in result.fetchall()]

@app.get("/stats", response_model=LogStats)
async def get_stats(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    QUERIES.labels(endpoint='stats').inc()
    
    if not start_time:
        start_time = datetime.utcnow() - timedelta(hours=24)
    if not end_time:
        end_time = datetime.utcnow()
    
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Total count
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM logs WHERE timestamp BETWEEN :start AND :end"),
            {"start": start_time, "end": end_time}
        )
        total = total_result.scalar()
        
        # By level
        level_result = await session.execute(
            text("""
                SELECT level, COUNT(*) FROM logs 
                WHERE timestamp BETWEEN :start AND :end 
                GROUP BY level
            """),
            {"start": start_time, "end": end_time}
        )
        by_level = {row[0]: row[1] for row in level_result.fetchall()}
        
        # By service
        service_result = await session.execute(
            text("""
                SELECT service, COUNT(*) FROM logs 
                WHERE timestamp BETWEEN :start AND :end 
                GROUP BY service ORDER BY COUNT(*) DESC LIMIT 20
            """),
            {"start": start_time, "end": end_time}
        )
        by_service = {row[0]: row[1] for row in service_result.fetchall()}
        
        return LogStats(
            total_logs=total,
            logs_by_level=by_level,
            logs_by_service=by_service,
            time_range={"start": start_time.isoformat(), "end": end_time.isoformat()}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
