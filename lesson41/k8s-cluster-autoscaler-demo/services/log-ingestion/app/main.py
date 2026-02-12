import asyncio
import json
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from kafka import KafkaProducer
import redis
import structlog
from prometheus_client import Counter, Histogram, generate_latest

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Prometheus metrics
REQUESTS_TOTAL = Counter('log_ingestion_requests_total', 'Total log ingestion requests', ['status'])
REQUEST_DURATION = Histogram('log_ingestion_request_duration_seconds', 'Request duration')

# Global clients
kafka_producer: Optional[KafkaProducer] = None
redis_client: Optional[redis.Redis] = None

class LogEntry(BaseModel):
    level: str = Field(..., pattern="^(DEBUG|INFO|WARN|ERROR|FATAL)$")
    message: str = Field(..., min_length=1, max_length=10000)
    service: str = Field(..., min_length=1, max_length=100)
    timestamp: Optional[float] = None
    metadata: Optional[dict] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global kafka_producer, redis_client
    
    logger.info("initializing_kafka_producer")
    kafka_producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=3,
        acks='all'
    )
    
    logger.info("initializing_redis_client")
    redis_client = redis.Redis(
        host='redis',
        port=6379,
        decode_responses=True,
        socket_connect_timeout=5
    )
    
    yield
    
    # Shutdown
    if kafka_producer:
        kafka_producer.close()
    if redis_client:
        redis_client.close()

app = FastAPI(
    title="Log Ingestion Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/logs")
async def ingest_log(log_entry: LogEntry, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    try:
        # Add timestamp if not provided
        if not log_entry.timestamp:
            log_entry.timestamp = time.time()
        
        # Publish to Kafka
        log_data = log_entry.model_dump()
        kafka_producer.send('logs', value=log_data)
        
        # Increment counter in Redis
        redis_client.incr(f"log_count:{log_entry.level}")
        
        # Background task: update recent logs cache
        background_tasks.add_task(cache_recent_log, log_data)
        
        REQUESTS_TOTAL.labels(status='success').inc()
        REQUEST_DURATION.observe(time.time() - start_time)
        
        logger.info("log_ingested", level=log_entry.level, service=log_entry.service)
        
        return {"status": "accepted", "id": str(int(log_entry.timestamp * 1000))}
    
    except Exception as e:
        REQUESTS_TOTAL.labels(status='error').inc()
        logger.error("log_ingestion_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to ingest log")

async def cache_recent_log(log_data: dict):
    """Cache recent logs for quick retrieval"""
    try:
        redis_client.lpush("recent_logs", json.dumps(log_data))
        redis_client.ltrim("recent_logs", 0, 99)  # Keep last 100 logs
    except Exception as e:
        logger.error("cache_update_failed", error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Kafka connectivity
        kafka_producer.bootstrap_connected()
        
        # Check Redis connectivity
        redis_client.ping()
        
        return {"status": "healthy", "dependencies": {"kafka": "up", "redis": "up"}}
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
