from datetime import datetime
from typing import Optional
import json
import os
import asyncio
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
import redis.asyncio as aioredis

app = FastAPI(title="Log Ingestion API")
logger = logging.getLogger(__name__)

# Metrics
requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
logs_ingested = Counter('logs_ingested_total', 'Total logs ingested', ['level'])

kafka_producer: Optional[AIOKafkaProducer] = None
redis_client: Optional[aioredis.Redis] = None
kafka_connected = False
redis_connected = False

class LogEntry(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    service: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    metadata: dict = Field(default_factory=dict)

async def connect_kafka_with_retry(max_retries=5, delay=5):
    """Connect to Kafka with retry logic"""
    global kafka_producer, kafka_connected
    
    for attempt in range(max_retries):
        try:
            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
                value_serializer=lambda v: json.dumps(v).encode(),
                request_timeout_ms=5000
            )
            await kafka_producer.start()
            kafka_connected = True
            logger.info("Successfully connected to Kafka")
            return True
        except (KafkaConnectionError, Exception) as e:
            logger.warning(f"Kafka connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Failed to connect to Kafka after all retries. API will continue but logs cannot be sent to Kafka.")
                kafka_connected = False
                return False

async def connect_redis_with_retry(max_retries=5, delay=5):
    """Connect to Redis with retry logic"""
    global redis_client, redis_connected
    
    for attempt in range(max_retries):
        try:
            redis_client = await aioredis.from_url(
                f"redis://{os.getenv('REDIS_HOST', 'redis')}:6379",
                socket_connect_timeout=5
            )
            await redis_client.ping()
            redis_connected = True
            logger.info("Successfully connected to Redis")
            return True
        except Exception as e:
            logger.warning(f"Redis connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Failed to connect to Redis after all retries. API will continue but caching will be unavailable.")
                redis_connected = False
                return False

@app.on_event("startup")
async def startup():
    """Startup with graceful degradation - allow API to start even if dependencies are unavailable"""
    # Try to connect to Kafka and Redis, but don't fail if they're unavailable
    await asyncio.gather(
        connect_kafka_with_retry(),
        connect_redis_with_retry(),
        return_exceptions=True
    )

@app.on_event("shutdown")
async def shutdown():
    if kafka_producer:
        await kafka_producer.stop()
    if redis_client:
        await redis_client.close()

@app.post("/api/v1/logs", status_code=201)
@request_duration.time()
async def ingest_log(log: LogEntry):
    global kafka_connected, redis_connected
    
    # Convert to dict, handling datetime serialization
    try:
        data = log.model_dump(mode='json')
    except (AttributeError, TypeError):
        # Fallback for Pydantic v1
        data = log.dict()
        # Convert datetime to ISO string
        if 'timestamp' in data and isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
    data['ingested_at'] = datetime.utcnow().isoformat()
    
    # Try to send to Kafka if available
    if kafka_producer and kafka_connected:
        try:
            await kafka_producer.send("logs-raw", value=data)
            logs_ingested.labels(level=log.level).inc()
        except Exception as e:
            logger.error(f"Failed to send log to Kafka: {e}")
            kafka_connected = False
            # Try to reconnect in background
            asyncio.create_task(connect_kafka_with_retry(max_retries=1, delay=2))
    else:
        logger.warning("Kafka not available, log not sent to Kafka")
    
    # Try to cache in Redis if available
    if redis_client and redis_connected:
        try:
            await redis_client.lpush(f"recent:{log.service}", json.dumps(data))
            await redis_client.ltrim(f"recent:{log.service}", 0, 99)
        except Exception as e:
            logger.error(f"Failed to cache log in Redis: {e}")
            redis_connected = False
            # Try to reconnect in background
            asyncio.create_task(connect_redis_with_retry(max_retries=1, delay=2))
    
    # Always return success if we at least tried to process the log
    requests_total.labels(method='POST', endpoint='/logs', status='200').inc()
    return {
        "status": "accepted",
        "kafka_available": kafka_connected,
        "redis_available": redis_connected
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "kafka_connected": kafka_connected,
        "redis_connected": redis_connected
    }

@app.get("/ready")
async def ready():
    # API is ready if it can respond, even if dependencies are unavailable
    return {
        "status": "ready",
        "kafka_connected": kafka_connected,
        "redis_connected": redis_connected
    }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
