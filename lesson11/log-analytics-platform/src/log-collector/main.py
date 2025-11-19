import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from kafka import KafkaProducer
from kafka.errors import KafkaError
import redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configuration from ConfigMaps and Secrets
CONFIG = {
    "log_level": os.getenv("LOG_LEVEL", "info"),
    "batch_size": int(os.getenv("BATCH_SIZE", "1000")),
    "kafka_brokers": os.getenv("KAFKA_BROKERS", "kafka:9092"),
    "kafka_topic": os.getenv("KAFKA_TOPIC", "raw-logs"),
    "redis_host": os.getenv("REDIS_HOST", "redis"),
    "redis_port": int(os.getenv("REDIS_PORT", "6379")),
    "redis_password": os.getenv("REDIS_PASSWORD", ""),
    "api_key": os.getenv("API_KEY", ""),
}

# Logging configuration
logging.basicConfig(
    level=getattr(logging, CONFIG["log_level"].upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_RECEIVED = Counter('logs_received_total', 'Total logs received')
LOGS_SENT = Counter('logs_sent_total', 'Total logs sent to Kafka')
LOGS_FAILED = Counter('logs_failed_total', 'Total logs failed to send')
PROCESSING_TIME = Histogram('log_processing_seconds', 'Time spent processing logs')

# Global clients
kafka_producer: Optional[KafkaProducer] = None
redis_client: Optional[redis.Redis] = None

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., pattern="^(DEBUG|INFO|WARN|ERROR|FATAL)$")
    service: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=10000)
    metadata: dict = Field(default_factory=dict)
    trace_id: Optional[str] = None

class LogBatch(BaseModel):
    logs: list[LogEntry] = Field(..., max_length=5000)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global kafka_producer, redis_client
    
    # Initialize Kafka producer
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=CONFIG["kafka_brokers"].split(","),
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        logger.info(f"Connected to Kafka at {CONFIG['kafka_brokers']}")
    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        raise
    
    # Initialize Redis
    try:
        redis_client = redis.Redis(
            host=CONFIG["redis_host"],
            port=CONFIG["redis_port"],
            password=CONFIG["redis_password"] or None,
            decode_responses=True
        )
        redis_client.ping()
        logger.info(f"Connected to Redis at {CONFIG['redis_host']}")
    except redis.RedisError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    
    yield
    
    # Cleanup
    if kafka_producer:
        kafka_producer.close()
    if redis_client:
        redis_client.close()

app = FastAPI(
    title="Log Collector Service",
    description="Ingests logs and forwards to Kafka for processing",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "log-collector"}

@app.get("/ready")
async def readiness_check():
    try:
        # Check Kafka
        kafka_producer.bootstrap_connected()
        # Check Redis
        redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/logs")
async def ingest_log(log: LogEntry, background_tasks: BackgroundTasks):
    LOGS_RECEIVED.inc()
    
    with PROCESSING_TIME.time():
        try:
            log_dict = log.model_dump()
            log_dict['ingested_at'] = datetime.utcnow().isoformat()
            
            # Send to Kafka
            future = kafka_producer.send(CONFIG["kafka_topic"], log_dict)
            future.get(timeout=10)
            
            LOGS_SENT.inc()
            
            # Update Redis counter
            redis_client.incr(f"logs:{log.service}:count")
            
            return {"status": "accepted", "trace_id": log.trace_id}
        except Exception as e:
            LOGS_FAILED.inc()
            logger.error(f"Failed to process log: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/logs/batch")
async def ingest_batch(batch: LogBatch):
    LOGS_RECEIVED.inc(len(batch.logs))
    
    with PROCESSING_TIME.time():
        success_count = 0
        failed_count = 0
        
        for log in batch.logs:
            try:
                log_dict = log.model_dump()
                log_dict['ingested_at'] = datetime.utcnow().isoformat()
                kafka_producer.send(CONFIG["kafka_topic"], log_dict)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send log: {e}")
                failed_count += 1
        
        # Flush all messages
        kafka_producer.flush()
        
        LOGS_SENT.inc(success_count)
        LOGS_FAILED.inc(failed_count)
        
        return {
            "status": "completed",
            "success": success_count,
            "failed": failed_count
        }

@app.get("/stats")
async def get_stats():
    # Get stats from Redis
    keys = redis_client.keys("logs:*:count")
    stats = {}
    for key in keys:
        service = key.split(":")[1]
        stats[service] = int(redis_client.get(key) or 0)
    return {"stats": stats}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
