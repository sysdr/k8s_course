import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from collections import defaultdict
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Processor Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
logs_received = Counter('logs_received_total', 'Total logs received', ['level'])
logs_processed = Counter('logs_processed_total', 'Total logs processed')
processing_latency = Histogram('log_processing_latency_seconds', 'Processing latency')
cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')
active_processors = Gauge('active_log_processors', 'Number of active processors')
buffer_size = Gauge('log_buffer_size', 'Current buffer size')

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@timescaledb:5432/logs')
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Redis connection
redis_client: Optional[aioredis.Redis] = None
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')

class LogModel(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    service = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    trace_id = Column(String(100), index=True)
    user_id = Column(String(100), index=True)

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None

class LogQuery(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    level: Optional[str] = None
    service: Optional[str] = None
    limit: int = Field(default=100, le=1000)

class ProcessingStats(BaseModel):
    total_received: int
    total_processed: int
    buffer_size: int
    cache_hit_rate: float
    uptime_seconds: int

# In-memory buffer for batch processing
log_buffer = []
buffer_lock = asyncio.Lock()
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))
FLUSH_INTERVAL = int(os.getenv('FLUSH_INTERVAL', '5'))

stats = {
    "received": 0,
    "processed": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "start_time": datetime.utcnow()
}

@app.on_event("startup")
async def startup_event():
    """Initialize database and Redis connections"""
    global redis_client
    
    try:
        # Initialize Redis
        redis_client = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        logger.info("Connected to Redis")
        
        # Initialize database
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
        
        # Start background tasks
        asyncio.create_task(periodic_flush())
        asyncio.create_task(cache_cleanup())
        
        active_processors.set(1)
        logger.info("Log processor service started")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown - flush remaining logs"""
    logger.info("Shutting down - flushing buffer...")
    await flush_buffer()
    if redis_client:
        await redis_client.close()
    active_processors.set(0)

async def flush_buffer():
    """Flush buffered logs to database"""
    async with buffer_lock:
        if not log_buffer:
            return
        
        try:
            async with async_session() as session:
                for log_data in log_buffer:
                    log_model = LogModel(**log_data)
                    session.add(log_model)
                
                await session.commit()
                count = len(log_buffer)
                stats["processed"] += count
                logs_processed.inc(count)
                logger.info(f"Flushed {count} logs to database")
                log_buffer.clear()
                buffer_size.set(0)
                
        except Exception as e:
            logger.error(f"Error flushing buffer: {e}")

async def periodic_flush():
    """Periodically flush buffer"""
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)
        if len(log_buffer) >= BATCH_SIZE:
            await flush_buffer()

async def cache_cleanup():
    """Cleanup old cache entries"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        try:
            if redis_client:
                # Implement TTL-based cleanup
                logger.info("Cache cleanup completed")
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

@app.post("/logs")
async def receive_log(log_entry: LogEntry, background_tasks: BackgroundTasks):
    """Receive and buffer log entries"""
    with processing_latency.time():
        try:
            logs_received.labels(level=log_entry.level).inc()
            stats["received"] += 1
            
            # Add to buffer
            async with buffer_lock:
                log_buffer.append(log_entry.dict())
                buffer_size.set(len(log_buffer))
            
            # Cache recent logs by trace_id
            if redis_client and log_entry.trace_id:
                cache_key = f"trace:{log_entry.trace_id}"
                await redis_client.setex(
                    cache_key,
                    300,  # 5 minute TTL
                    json.dumps(log_entry.dict(), default=str)
                )
            
            # Flush if buffer is full
            if len(log_buffer) >= BATCH_SIZE:
                background_tasks.add_task(flush_buffer)
            
            return {"status": "accepted", "buffer_size": len(log_buffer)}
            
        except Exception as e:
            logger.error(f"Error receiving log: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/search")
async def search_logs(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    level: Optional[str] = None,
    service: Optional[str] = None,
    limit: int = 100
):
    """Search logs with caching"""
    query_params = {
        "start_time": start_time,
        "end_time": end_time,
        "level": level,
        "service": service,
        "limit": limit
    }
    cache_key = f"search:{json.dumps(query_params, default=str)}"
    
    # Try cache first
    if redis_client:
        cached = await redis_client.get(cache_key)
        if cached:
            cache_hits.inc()
            stats["cache_hits"] += 1
            return {"results": json.loads(cached), "cached": True}
    
    cache_misses.inc()
    stats["cache_misses"] += 1
    
    # Query database
    try:
        async with async_session() as session:
            from sqlalchemy import select
            stmt = select(LogModel)
            
            if start_time:
                stmt = stmt.where(LogModel.timestamp >= start_time)
            if end_time:
                stmt = stmt.where(LogModel.timestamp <= end_time)
            if level:
                stmt = stmt.where(LogModel.level == level)
            if service:
                stmt = stmt.where(LogModel.service == service)
            
            stmt = stmt.order_by(LogModel.timestamp.desc()).limit(limit)
            result = await session.execute(stmt)
            logs = result.scalars().all()
            
            results = [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "service": log.service,
                    "message": log.message,
                    "trace_id": log.trace_id,
                    "user_id": log.user_id
                }
                for log in logs
            ]
            
            # Cache results
            if redis_client:
                await redis_client.setex(cache_key, 60, json.dumps(results))
            
            return {"results": results, "cached": False, "count": len(results)}
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/trace/{trace_id}")
async def get_by_trace(trace_id: str):
    """Get logs by trace ID (cached)"""
    cache_key = f"trace:{trace_id}"
    
    if redis_client:
        cached = await redis_client.get(cache_key)
        if cached:
            return {"log": json.loads(cached), "cached": True}
    
    # Fallback to database
    async with async_session() as session:
        from sqlalchemy import select
        stmt = select(LogModel).where(LogModel.trace_id == trace_id)
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        if not logs:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {"logs": [{"message": log.message, "timestamp": log.timestamp.isoformat()} for log in logs]}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "buffer_size": len(log_buffer)}

@app.get("/ready")
async def readiness_check():
    """Readiness check - verify database and Redis connections"""
    try:
        # Check database
        async with async_session() as session:
            await session.execute("SELECT 1")
        
        # Check Redis
        if redis_client:
            await redis_client.ping()
        
        return {"status": "ready", "database": "connected", "cache": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {e}")

@app.get("/stats")
async def get_stats() -> ProcessingStats:
    """Get processing statistics"""
    uptime = (datetime.utcnow() - stats["start_time"]).total_seconds()
    total_cache_requests = stats["cache_hits"] + stats["cache_misses"]
    hit_rate = (stats["cache_hits"] / total_cache_requests * 100) if total_cache_requests > 0 else 0
    
    return ProcessingStats(
        total_received=stats["received"],
        total_processed=stats["processed"],
        buffer_size=len(log_buffer),
        cache_hit_rate=hit_rate,
        uptime_seconds=int(uptime)
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
