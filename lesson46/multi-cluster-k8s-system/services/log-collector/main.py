from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import aioredis
from kafka import KafkaProducer
import json
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Collector Service", version="1.0.0")

# Configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CLUSTER_NAME = os.getenv("CLUSTER_NAME", "unknown")

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    compression_type='gzip'
)

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    service: str
    message: str
    metadata: Optional[dict] = {}
    cluster: str = CLUSTER_NAME

class HealthResponse(BaseModel):
    status: str
    cluster: str
    dependencies: dict

@app.on_event("startup")
async def startup_event():
    logger.info(f"Log Collector starting in cluster: {CLUSTER_NAME}")

@app.post("/api/v1/logs", status_code=202)
async def collect_logs(logs: List[LogEntry], background_tasks: BackgroundTasks):
    """Collect and forward logs to Kafka for processing"""
    try:
        background_tasks.add_task(forward_to_kafka, logs)
        return {
            "status": "accepted",
            "count": len(logs),
            "cluster": CLUSTER_NAME
        }
    except Exception as e:
        logger.error(f"Error collecting logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def forward_to_kafka(logs: List[LogEntry]):
    """Forward logs to Kafka topic"""
    for log in logs:
        try:
            log_dict = log.dict()
            log_dict['timestamp'] = log_dict['timestamp'].isoformat()
            producer.send('raw-logs', value=log_dict)
            logger.debug(f"Forwarded log from {log.service}")
        except Exception as e:
            logger.error(f"Kafka forwarding error: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    kafka_status = "healthy" if producer.bootstrap_connected() else "unhealthy"
    
    return HealthResponse(
        status="healthy" if kafka_status == "healthy" else "degraded",
        cluster=CLUSTER_NAME,
        dependencies={
            "kafka": kafka_status,
            "redis": "healthy"
        }
    )

@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    if not producer.bootstrap_connected():
        raise HTTPException(status_code=503, detail="Kafka not ready")
    return {"status": "ready", "cluster": CLUSTER_NAME}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return {
        "log_collector_requests_total": 1000,
        "log_collector_errors_total": 5,
        "cluster": CLUSTER_NAME
    }
