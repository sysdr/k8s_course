"""Custom Prometheus metrics for the ingestor."""
from prometheus_client import Counter, Histogram, REGISTRY

EVENTS_RECEIVED = Counter(
    "log_ingestor_events_received_total",
    "Total log events received.",
    ["severity", "service"],
)

INGEST_LATENCY = Histogram(
    "log_ingestor_ingest_latency_seconds",
    "End-to-end ingest latency (validation + produce).",
    ["service"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

KAFKA_PRODUCE_ERRORS = Counter(
    "log_ingestor_kafka_produce_errors_total",
    "Kafka produce failures.",
    ["topic"],
)
