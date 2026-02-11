"""Kafka producer with OpenTelemetry context propagation (W3C traceparent)."""
import logging
import json
from confluent_kafka import Producer
from opentelemetry import context, trace
from opentelemetry.propagate import inject

logger = logging.getLogger(__name__)

import os
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:29092")
KAFKA_CONFIG: dict = {
    "bootstrap.servers": KAFKA_BROKERS,
    "acks": "all",                     # durability: wait for all ISR acks
    "linger.ms": 5,                    # micro-batch for throughput
    "compression.type": "lz4",
}


class KafkaProducer:
    """Singleton wrapper around confluent_kafka.Producer."""

    _instance: "KafkaProducer | None" = None
    _producer: Producer

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._producer = Producer(KAFKA_CONFIG)
        return cls._instance

    def produce(self, topic: str, key: str, value: dict, tracer: trace.Tracer) -> None:
        """Produce a message, injecting the current trace context into headers.

        The W3C *traceparent* header is what keeps the distributed trace
        stitched across the async Kafka boundary.  Without explicit injection
        here the consumer side will start an orphan span.
        """
        headers: dict[str, str] = {}
        inject(carrier=headers)          # writes traceparent + tracestate

        try:
            self._producer.produce(
                topic=topic,
                key=key.encode(),
                value=json.dumps(value).encode(),
                headers={k: v.encode() if isinstance(v, str) else v for k, v in headers.items()},
            )
            self._producer.poll(0)       # trigger delivery callbacks (non-blocking)
        except Exception as exc:
            logger.exception("Kafka produce failed for topic=%s: %s", topic, exc)
            raise

    def flush(self, timeout: float = 5.0) -> int:
        return self._producer.flush(timeout)
