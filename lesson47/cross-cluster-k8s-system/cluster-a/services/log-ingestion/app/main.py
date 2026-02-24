"""
Cross-Cluster Log Ingestion Service
Receives logs via HTTP and publishes to Kafka for cross-cluster processing
"""
import os
import logging
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from redis.asyncio import Redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import json
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('log_ingestion_requests_total', 'Total log ingestion requests', ['status'])
REQUEST_LATENCY = Histogram('log_ingestion_latency_seconds', 'Log ingestion latency')
KAFKA_PUBLISH_COUNT = Counter('kafka_publish_total', 'Total Kafka publishes', ['status'])

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'logs')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
CLUSTER_ID = os.getenv('CLUSTER_ID', 'cluster-a')

# Global resources
kafka_producer: Optional[AIOKafkaProducer] = None
redis_client: Optional[Redis] = None


class LogEntry(BaseModel):
    """Log entry schema with validation"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = Field(..., min_length=1, max_length=100)
    level: str = Field(..., pattern='^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    message: str = Field(..., min_length=1, max_length=10000)
    trace_id: Optional[str] = Field(None, max_length=64)
    metadata: Optional[dict] = Field(default_factory=dict)
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v and len(json.dumps(v)) > 50000:
            raise ValueError('Metadata too large (max 50KB)')
        return v


class HealthResponse(BaseModel):
    status: str
    cluster_id: str
    kafka_connected: bool
    redis_connected: bool
    timestamp: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global kafka_producer, redis_client
    
    # Startup
    logger.info(f"Starting Log Ingestion Service in {CLUSTER_ID}")
    
    try:
        # Initialize Kafka producer
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip',
            request_timeout_ms=30000,
            retry_backoff_ms=500
        )
        await kafka_producer.start()
        logger.info("Kafka producer connected")
        
        # Initialize Redis client (redis-py async)
        redis_client = Redis.from_url(
            REDIS_URL,
            encoding='utf-8',
            decode_responses=True,
            max_connections=20
        )
        await redis_client.ping()
        logger.info("Redis client connected")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Log Ingestion Service")
    
    if kafka_producer:
        await kafka_producer.stop()
    
    if redis_client:
        await redis_client.aclose()


app = FastAPI(
    title="Cross-Cluster Log Ingestion API",
    description="Production-grade log ingestion with Kafka publishing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    kafka_healthy = kafka_producer is not None
    redis_healthy = redis_client is not None
    
    if redis_healthy:
        try:
            await redis_client.ping()
        except Exception:
            redis_healthy = False
    
    status_code = "healthy" if (kafka_healthy and redis_healthy) else "degraded"
    
    return HealthResponse(
        status=status_code,
        cluster_id=CLUSTER_ID,
        kafka_connected=kafka_healthy,
        redis_connected=redis_healthy,
        timestamp=datetime.utcnow()
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    if not kafka_producer or not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    return {"status": "ready"}


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_log(log: LogEntry, request: Request):
    """
    Ingest a log entry and publish to Kafka
    
    This endpoint receives logs from various services, validates them,
    caches recent logs in Redis for quick queries, and publishes to Kafka
    for cross-cluster processing in Cluster B.
    """
    with REQUEST_LATENCY.time():
        try:
            # Enrich log with cluster information (use JSON-serializable dict for Kafka)
            log_data = log.model_dump(mode='json') if hasattr(log, 'model_dump') else log.dict()
            if isinstance(log_data.get('timestamp'), datetime):
                log_data['timestamp'] = log_data['timestamp'].isoformat()
            log_data['cluster_id'] = CLUSTER_ID
            log_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            # Extract trace ID from headers if present
            if not log.trace_id and 'x-trace-id' in request.headers:
                log_data['trace_id'] = request.headers['x-trace-id']
            
            # Publish to Kafka
            try:
                await kafka_producer.send_and_wait(KAFKA_TOPIC, value=log_data)
                KAFKA_PUBLISH_COUNT.labels(status='success').inc()
                logger.info(f"Published log to Kafka: {log.service} - {log.level}")
            except KafkaError as e:
                KAFKA_PUBLISH_COUNT.labels(status='error').inc()
                logger.error(f"Kafka publish failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to publish to Kafka"
                )
            
            # Cache recent logs in Redis (last 1000 per service)
            try:
                cache_key = f"logs:{log.service}:recent"
                await redis_client.lpush(cache_key, json.dumps(log_data))
                await redis_client.ltrim(cache_key, 0, 999)
                await redis_client.expire(cache_key, 3600)  # 1 hour TTL
            except Exception as e:
                logger.warning(f"Redis caching failed: {e}")
                # Non-critical, continue
            
            REQUEST_COUNT.labels(status='success').inc()
            
            return {
                "status": "accepted",
                "cluster_id": CLUSTER_ID,
                "trace_id": log_data.get('trace_id')
            }
            
        except HTTPException:
            REQUEST_COUNT.labels(status='error').inc()
            raise
        except Exception as e:
            REQUEST_COUNT.labels(status='error').inc()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@app.post("/ingest/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch(logs: List[LogEntry]):
    """Batch ingest multiple log entries"""
    if len(logs) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size exceeds limit (max 1000)"
        )
    
    results = []
    for log in logs:
        try:
            log_data = log.model_dump(mode='json') if hasattr(log, 'model_dump') else log.dict()
            if isinstance(log_data.get('timestamp'), datetime):
                log_data['timestamp'] = log_data['timestamp'].isoformat()
            log_data['cluster_id'] = CLUSTER_ID
            log_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            await kafka_producer.send_and_wait(KAFKA_TOPIC, value=log_data)
            results.append({"status": "accepted", "service": log.service})
            KAFKA_PUBLISH_COUNT.labels(status='success').inc()
        except Exception as e:
            logger.error(f"Batch item failed: {e}")
            results.append({"status": "failed", "service": log.service})
            KAFKA_PUBLISH_COUNT.labels(status='error').inc()
    
    REQUEST_COUNT.labels(status='batch').inc()
    
    return {
        "total": len(logs),
        "accepted": sum(1 for r in results if r['status'] == 'accepted'),
        "failed": sum(1 for r in results if r['status'] == 'failed'),
        "results": results
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    try:
        # Get total logs cached in Redis
        services = await redis_client.keys("logs:*:recent")
        total_cached = 0
        service_counts = {}
        
        for service_key in services:
            count = await redis_client.llen(service_key)
            total_cached += count
            service_name = service_key.split(':')[1]
            service_counts[service_name] = count
        
        return {
            "cluster_id": CLUSTER_ID,
            "total_cached_logs": total_cached,
            "services": service_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
