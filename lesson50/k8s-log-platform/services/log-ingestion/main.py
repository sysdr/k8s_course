#!/usr/bin/env python3
"""
Log Ingestion Service — FastAPI async entry point for the log processing pipeline.
Accepts structured log events, validates schema, publishes to Kafka.
"""
import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import PlainTextResponse

from kafka_producer import KafkaProducerClient
from models import LogEvent, LogEventBatch, HealthResponse
from config import Settings

settings = Settings()
structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger(__name__)

INGESTED_TOTAL    = Counter("log_ingestion_total", "Total log events ingested", ["service", "level"])
INGESTION_LATENCY = Histogram("log_ingestion_duration_seconds", "Ingestion latency", buckets=[.005,.01,.025,.05,.1,.25,.5,1,2.5])
KAFKA_ERRORS      = Counter("log_kafka_publish_errors_total", "Kafka publish failures")

kafka_client: KafkaProducerClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global kafka_client
    logger.info("startup.begin", brokers=settings.kafka_brokers)
    kafka_client = KafkaProducerClient(brokers=settings.kafka_brokers)
    await kafka_client.start()
    # Ensure topic exists so processor can subscribe (Kafka auto-create on first produce)
    try:
        await kafka_client.publish(
            topic=settings.kafka_topic,
            key="__init__",
            value={"event_id": "00000000-0000-0000-0000-000000000000", "service": "__init__", "level": "INFO", "message": "topic init", "timestamp": "1970-01-01T00:00:00Z", "ingested_at": 0},
        )
    except Exception:
        pass
    logger.info("startup.complete")
    yield
    logger.info("shutdown.begin")
    if kafka_client:
        await kafka_client.stop()
    logger.info("shutdown.complete")


app = FastAPI(
    title="Log Ingestion Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    with structlog.contextvars.bound_contextvars(request_id=request_id):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
async def health() -> HealthResponse:
    kafka_ok = kafka_client is not None and kafka_client.is_connected()
    if not kafka_ok:
        raise HTTPException(status_code=503, detail="Kafka unavailable")
    return HealthResponse(status="ok", kafka_connected=True)


@app.get("/readyz", tags=["ops"])
async def readiness():
    if kafka_client is None or not kafka_client.is_connected():
        raise HTTPException(status_code=503, detail="Not ready")
    return {"ready": True}


@app.get("/metrics", response_class=PlainTextResponse, tags=["ops"])
async def metrics():
    return PlainTextResponse(generate_latest())


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED, tags=["ingestion"])
async def ingest_single(event: LogEvent, request: Request):
    start = time.monotonic()
    try:
        event_dict = event.model_dump(mode="json")
        event_dict["ingested_at"] = time.time()
        event_dict["source_ip"] = request.client.host if request.client else "unknown"
        await kafka_client.publish(topic=settings.kafka_topic, key=event.service, value=event_dict)
        INGESTED_TOTAL.labels(service=event.service, level=event.level).inc()
        logger.info("event.ingested", service=event.service, level=event.level)
        return {"accepted": True, "event_id": event.event_id}
    except Exception as exc:
        KAFKA_ERRORS.inc()
        logger.error("event.ingest_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Ingestion failed")
    finally:
        INGESTION_LATENCY.observe(time.monotonic() - start)


@app.post("/ingest/batch", status_code=status.HTTP_202_ACCEPTED, tags=["ingestion"])
async def ingest_batch(batch: LogEventBatch, request: Request):
    if len(batch.events) > settings.max_batch_size:
        raise HTTPException(status_code=400, detail=f"Batch exceeds max size {settings.max_batch_size}")
    tasks = [
        kafka_client.publish(
            topic=settings.kafka_topic,
            key=e.service,
            value={**e.model_dump(mode="json"), "ingested_at": time.time()},
        )
        for e in batch.events
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    failed = sum(1 for r in results if isinstance(r, Exception))
    if failed:
        KAFKA_ERRORS.inc(failed)
    accepted = len(batch.events) - failed
    for e in batch.events:
        INGESTED_TOTAL.labels(service=e.service, level=e.level).inc()
    return {"accepted": accepted, "failed": failed}
