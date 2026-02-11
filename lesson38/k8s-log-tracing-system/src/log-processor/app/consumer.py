"""
Kafka consumer loop with OpenTelemetry context extraction.

Key insight: confluent_kafka does NOT auto-propagate headers into OTel context.
We must manually extract the W3C traceparent from each message's headers and
set it as the parent context before starting the processing span.  This is
the single most common place distributed traces break in production.
"""
import json
import logging
import os
import uuid
import redis
from confluent_kafka import Consumer, KafkaError
from opentelemetry import context, trace
from opentelemetry.propagate import extract

from .database import Session
from .models import LogRecord

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:29092")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BROKERS,
    "group.id":          "log-processor-cg",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
    "fetch.min.bytes":    1,
    "max.poll.interval.ms": 300000,
}

# Redis client for analytics updates
_redis = redis.from_url(REDIS_URL, decode_responses=True)

def extract_context_from_headers(headers: list[tuple[str, bytes]]) -> context.Context:
    """Convert Kafka binary headers → dict carrier → OTel context."""
    carrier = {k: v.decode() for k, v in (headers or []) if v}
    return extract(carrier)


def run_consumer(tracer: trace.Tracer, shutdown_event):
    """Blocking consumer loop; call from a background thread."""
    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe(["log-events"])
    logger.info("Consumer subscribed to log-events.")

    while not shutdown_event.is_set():
        messages = consumer.poll(timeout=1.0)
        if messages is None:
            continue
        if messages.error():
            if messages.error().code() == KafkaError._PARTITION_EOF:
                continue
            logger.error("Kafka error: %s", messages.error())
            continue

        # ── restore distributed trace context ─────────────────────────────
        parent_ctx = extract_context_from_headers(messages.headers())

        with tracer.start_as_current_span(
            "kafka.consume.process",
            context=parent_ctx,
        ) as span:
            try:
                payload = json.loads(messages.value().decode())
                span.set_attribute("event.id",       payload.get("event_id", "unknown"))
                span.set_attribute("event.service",  payload.get("service", "unknown"))

                _persist(payload)
                span.set_status(trace.Status(trace.StatusCode.OK))
            except Exception as exc:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                span.record_exception(exc)
                logger.exception("Failed to process message: %s", exc)

    consumer.close()
    logger.info("Consumer closed.")


def _persist(payload: dict) -> None:
    """Write one LogRecord to PostgreSQL and update Redis analytics."""
    severity = payload.get("severity", "INFO")
    service = payload.get("service", "unknown")
    
    # Update Redis analytics counters FIRST (so dashboard works even if DB fails)
    try:
        _redis.hincrby("analytics:counts:severity", severity, 1)
        _redis.hincrby("analytics:counts:service", service, 1)
        
        # Store recent trace IDs (keep last 50)
        trace_id = payload.get("trace_id")
        if trace_id:
            _redis.lpush("analytics:recent_traces", trace_id)
            _redis.ltrim("analytics:recent_traces", 0, 49)  # Keep only last 50
    except Exception as e:
        logger.warning("Failed to update Redis analytics: %s", e)
    
    # Persist to PostgreSQL (with error handling for duplicates)
    try:
        event_id = payload.get("event_id")
        if not event_id or event_id == "unknown":
            event_id = str(uuid.uuid4())
        
        with Session() as session:
            record = LogRecord(
                event_id = event_id,
                trace_id =payload.get("trace_id"),
                severity =severity,
                service  =service,
                message  =payload.get("message", ""),
                event_metadata =json.dumps(payload.get("metadata")) if payload.get("metadata") else None,
            )
            session.add(record)
            session.commit()
    except Exception as e:
        logger.warning("Failed to persist to database (non-fatal): %s", e)
        # Don't re-raise - Redis update already succeeded