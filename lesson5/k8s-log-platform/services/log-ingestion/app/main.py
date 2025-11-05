import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from aiokafka import AIOKafkaProducer
import structlog
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('log_ingestion_requests_total', 'Total log ingestion requests', ['status'])
REQUEST_LATENCY = Histogram('log_ingestion_request_duration_seconds', 'Request latency')
KAFKA_PUBLISH_SUCCESS = Counter('kafka_publish_success_total', 'Successful Kafka publishes')
KAFKA_PUBLISH_FAILURE = Counter('kafka_publish_failure_total', 'Failed Kafka publishes')

app = FastAPI(title="Log Ingestion Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "application-logs")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql+asyncpg://postgres:SecurePassword123!@postgresql.log-platform.svc.cluster.local:5432/logs")

# Global Kafka producer
kafka_producer: Optional[AIOKafkaProducer] = None

# Database connection for stats
db_engine = None
db_session_factory = None


class LogEntry(BaseModel):
    level: str = Field(..., description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    message: str = Field(..., min_length=1, max_length=10000)
    service: str = Field(..., min_length=1, max_length=100)
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None
    
    @validator('level')
    def validate_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Level must be one of {allowed_levels}')
        return v.upper()
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()


@app.on_event("startup")
async def startup_event():
    """Initialize Kafka producer and database connection on startup"""
    global kafka_producer, db_engine, db_session_factory
    try:
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            compression_type="gzip",
            max_batch_size=16384,
            linger_ms=10,
        )
        await kafka_producer.start()
        logger.info("kafka_producer_started", bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        
        # Initialize database connection for stats
        try:
            db_engine = create_async_engine(
                POSTGRES_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            db_session_factory = sessionmaker(
                db_engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("database_connection_initialized")
        except Exception as db_error:
            logger.warning("database_connection_failed", error=str(db_error))
            # Continue without database - stats will return empty/default values
    except Exception as e:
        logger.error("kafka_producer_startup_failed", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Kafka producer on shutdown"""
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()
        logger.info("kafka_producer_stopped")


@app.post("/api/v1/logs")
async def ingest_log(log_entry: LogEntry):
    """
    Ingest a log entry and publish to Kafka
    """
    with REQUEST_LATENCY.time():
        try:
            # Convert to dict and handle datetime serialization
            log_data = {
                "level": log_entry.level,
                "message": log_entry.message,
                "service": log_entry.service,
                "timestamp": log_entry.timestamp.isoformat() if isinstance(log_entry.timestamp, datetime) else (log_entry.timestamp or datetime.utcnow()).isoformat(),
                "metadata": log_entry.metadata or {}
            }
            
            # Publish to Kafka
            await kafka_producer.send_and_wait(
                KAFKA_TOPIC,
                value=log_data,
                key=log_entry.service.encode('utf-8')
            )
            
            KAFKA_PUBLISH_SUCCESS.inc()
            REQUEST_COUNT.labels(status='success').inc()
            
            try:
                logger.info(
                    "log_ingested",
                    service=log_entry.service,
                    level=log_entry.level,
                    message_length=len(log_entry.message)
                )
            except Exception:
                pass  # Don't fail if logging fails
            
            return {
                "status": "success",
                "message": "Log ingested successfully",
                "timestamp": log_data["timestamp"]
            }
        
        except Exception as e:
            KAFKA_PUBLISH_FAILURE.inc()
            REQUEST_COUNT.labels(status='error').inc()
            try:
                logger.error("log_ingestion_failed", error=str(e))
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to ingest log: {str(e)}")


@app.post("/api/v1/logs/batch")
@REQUEST_LATENCY.time()
async def ingest_logs_batch(log_entries: list[LogEntry]):
    """
    Batch ingest multiple log entries
    """
    if len(log_entries) > 1000:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 1000 entries")
    
    try:
        tasks = []
        for log_entry in log_entries:
            # Convert to dict and handle datetime serialization
            log_data = {
                "level": log_entry.level,
                "message": log_entry.message,
                "service": log_entry.service,
                "timestamp": log_entry.timestamp.isoformat() if isinstance(log_entry.timestamp, datetime) else (log_entry.timestamp or datetime.utcnow()).isoformat(),
                "metadata": log_entry.metadata or {}
            }
            tasks.append(
                kafka_producer.send(
                    KAFKA_TOPIC,
                    value=log_data,
                    key=log_entry.service.encode('utf-8')
                )
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Check for any exceptions
        for result in results:
            if isinstance(result, Exception):
                raise result
        
        KAFKA_PUBLISH_SUCCESS.inc(len(log_entries))
        REQUEST_COUNT.labels(status='success').inc()
        
        logger.info("batch_logs_ingested", count=len(log_entries))
        
        return {
            "status": "success",
            "message": f"{len(log_entries)} logs ingested successfully",
            "count": len(log_entries)
        }
        
    except Exception as e:
        KAFKA_PUBLISH_FAILURE.inc(len(log_entries))
        REQUEST_COUNT.labels(status='error').inc()
        logger.error("batch_log_ingestion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to ingest logs: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "log-ingestion"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if kafka_producer and kafka_producer._closed:
        raise HTTPException(status_code=503, detail="Kafka producer not ready")
    return {"status": "ready", "service": "log-ingestion"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/api/v1/stats")
async def get_stats():
    """Get log statistics from database"""
    try:
        if not db_session_factory:
            # Return default stats if database not available
            return {
                "total": 0,
                "byLevel": {},
                "byService": {},
                "timeline": []
            }
        
        async with db_session_factory() as session:
            # Get total count
            total_result = await session.execute(text("SELECT COUNT(*) FROM logs"))
            total = total_result.scalar() or 0
            
            # Get counts by level
            level_result = await session.execute(
                text("SELECT level, COUNT(*) as count FROM logs GROUP BY level")
            )
            by_level = {row[0]: row[1] for row in level_result.fetchall()}
            
            # Get counts by service
            service_result = await session.execute(
                text("SELECT service, COUNT(*) as count FROM logs GROUP BY service")
            )
            by_service = {row[0]: row[1] for row in service_result.fetchall()}
            
            # Get timeline data (last 24 hours, grouped by hour)
            hours_ago = datetime.utcnow() - timedelta(hours=24)
            timeline_result = await session.execute(
                text("""
                    SELECT 
                        DATE_TRUNC('hour', timestamp) as hour,
                        COUNT(*) as count
                    FROM logs
                    WHERE timestamp >= :hours_ago
                    GROUP BY hour
                    ORDER BY hour
                """),
                {"hours_ago": hours_ago}
            )
            timeline = []
            for row in timeline_result.fetchall():
                hour_dt = row[0]
                if isinstance(hour_dt, datetime):
                    timeline.append({
                        "timestamp": f"{hour_dt.hour}:00",
                        "count": row[1]
                    })
            
            return {
                "total": total,
                "byLevel": by_level,
                "byService": by_service,
                "timeline": timeline if timeline else generate_default_timeline()
            }
            
    except Exception as e:
        logger.error("stats_fetch_failed", error=str(e))
        # Return default stats on error
        return {
            "total": 0,
            "byLevel": {},
            "byService": {},
            "timeline": generate_default_timeline()
        }


def generate_default_timeline():
    """Generate default timeline data"""
    timeline = []
    now = datetime.utcnow()
    for i in range(23, -1, -1):
        hour = (now - timedelta(hours=i)).hour
        timeline.append({
            "timestamp": f"{hour}:00",
            "count": 0
        })
    return timeline


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
