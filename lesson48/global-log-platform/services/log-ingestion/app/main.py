"""
Log Ingestion Service — FastAPI
Receives log events, validates, publishes to Kafka, exposes Prometheus metrics.
"""
import asyncio
import json
import logging
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Optional

# In-memory ring buffer of recently ingested events for GET /logs/recent (aggregator/dashboard)
RECENT_EVENTS: deque = deque(maxlen=500)

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC     = os.getenv("KAFKA_TOPIC", "raw-logs")
REGION          = os.getenv("REGION", "us-east")

# Prometheus metrics
INGESTION_COUNTER = Counter("log_ingestion_total", "Total log events ingested", ["region", "level"])
INGESTION_LATENCY = Histogram("log_ingestion_duration_seconds", "Ingestion end-to-end latency",
                               ["region"], buckets=[.005, .01, .025, .05, .1, .25, .5, 1, 2.5])
KAFKA_ERRORS      = Counter("kafka_publish_errors_total", "Kafka publish failures", ["region"])

producer: Optional[AIOKafkaProducer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    logger.info("Starting Kafka producer — bootstrap: %s", KAFKA_BOOTSTRAP)
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
        compression_type="gzip",
        max_batch_size=65536,
        linger_ms=5,
    )
    await producer.start()
    logger.info("Kafka producer ready")
    yield
    logger.info("Shutting down Kafka producer")
    await producer.stop()

app = FastAPI(title="Log Ingestion Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class LogEvent(BaseModel):
    service:   str = Field(..., min_length=1, max_length=128)
    level:     str = Field(..., pattern="^(DEBUG|INFO|WARN|ERROR|FATAL)$")
    message:   str = Field(..., min_length=1, max_length=8192)
    timestamp: Optional[float] = None
    trace_id:  Optional[str]   = None
    metadata:  Optional[dict]  = {}

    @validator("timestamp", pre=True, always=True)
    def default_timestamp(cls, v):
        return v or time.time()


class BatchRequest(BaseModel):
    events: list[LogEvent] = Field(..., min_items=1, max_items=1000)


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_single(event: LogEvent):
    return await _publish_events([event])


@app.post("/ingest/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch(batch: BatchRequest):
    return await _publish_events(batch.events)


async def _publish_events(events: list[LogEvent]) -> dict:
    if producer is None:
        raise HTTPException(status_code=503, detail="Kafka producer not initialised")
    start = time.perf_counter()
    published = 0
    futures = []
    for event in events:
        payload = event.dict()
        payload["region"] = REGION
        try:
            fut = await producer.send(KAFKA_TOPIC, value=payload, key=event.service.encode())
            futures.append((fut, event.level, payload))
        except Exception as exc:
            KAFKA_ERRORS.labels(region=REGION).inc()
            logger.error("Kafka send error: %s", exc)

    for fut, level, payload in futures:
        try:
            await asyncio.wait_for(asyncio.shield(fut), timeout=5.0)
            INGESTION_COUNTER.labels(region=REGION, level=level).inc()
            published += 1
            RECENT_EVENTS.appendleft(payload)
        except asyncio.TimeoutError:
            KAFKA_ERRORS.labels(region=REGION).inc()
            logger.warning("Kafka ack timeout for event")

    elapsed = time.perf_counter() - start
    INGESTION_LATENCY.labels(region=REGION).observe(elapsed)
    return {"accepted": published, "total": len(events), "region": REGION}


@app.get("/logs/recent")
async def logs_recent():
    """Return recently ingested events for aggregator/dashboard (in-memory ring buffer)."""
    return {"events": list(RECENT_EVENTS)}


@app.get("/health/live")
async def liveness():
    return {"status": "alive", "region": REGION}


@app.get("/health/ready")
async def readiness():
    if producer is None:
        raise HTTPException(status_code=503, detail="Producer not ready")
    return {"status": "ready", "region": REGION}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=1)
