"""
Log Ingestor — entry-point.

Responsibilities:
  1. Validate inbound log events (Pydantic).
  2. Emit a child span for Kafka produce (OTel).
  3. Produce to Kafka with W3C traceparent header injection.
  4. Expose /health, /ready, /metrics endpoints.
"""
import uuid
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from .models import LogEvent, LogEventResponse
from .kafka_producer import KafkaProducer
from .metrics import EVENTS_RECEIVED, INGEST_LATENCY, KAFKA_PRODUCE_ERRORS

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","svc":"log-ingestor","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# ── OpenTelemetry bootstrap ───────────────────────────────────────────────────
OTLP_ENDPOINT = "http://otel-collector.observability.svc.cluster.local:4317"

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint=OTLP_ENDPOINT),
        export_timeout_millis=1000,      # non-blocking: never stall the request
    )
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("log-ingestor")

# ── Kafka singleton ───────────────────────────────────────────────────────────
kafka: KafkaProducer | None = None

TOPIC = "log-events"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global kafka
    kafka = KafkaProducer()
    logger.info("Kafka producer initialised.")
    yield
    kafka.flush()
    logger.info("Kafka producer flushed and shut down.")


app = FastAPI(title="Log Ingestor", version="1.0.0", lifespan=lifespan)
FastAPIInstrumentor().instrument_app(app)  # auto-instruments every route


# ── routes ────────────────────────────────────────────────────────────────────

@app.post("/ingest", response_model=LogEventResponse, status_code=202)
async def ingest(event: LogEvent, request: Request):
    """Ingest a single log event: validate → span → produce."""
    event_id = str(uuid.uuid4())
    start = time.perf_counter()

    # pull the active trace context (set by the FastAPI instrumentor)
    span_ctx = trace.get_current_span().get_span_context()
    t_id = format(span_ctx.trace_id, "032x") if span_ctx.is_valid else event_id

    event.trace_id = event.trace_id or t_id

    with tracer.start_as_current_span("kafka.produce") as produce_span:
        produce_span.set_attribute("event.id", event_id)
        produce_span.set_attribute("event.severity", event.severity.value)
        produce_span.set_attribute("event.service", event.service)
        try:
            kafka.produce(TOPIC, key=event.service, value=event.model_dump(mode="json"), tracer=tracer)
        except Exception:
            KAFKA_PRODUCE_ERRORS.labels(topic=TOPIC).inc()
            produce_span.set_status(trace.Status(trace.StatusCode.ERROR, "Kafka produce failed"))
            raise

    elapsed = time.perf_counter() - start
    EVENTS_RECEIVED.labels(severity=event.severity.value, service=event.service).inc()
    INGEST_LATENCY.labels(service=event.service).observe(elapsed)

    return LogEventResponse(event_id=event_id, accepted=True, trace_id=t_id)


@app.get("/")
async def root():
    return {
        "service": "log-ingestor",
        "version": "1.0.0",
        "endpoints": {
            "ingest": "POST /ingest",
            "health": "GET /health",
            "metrics": "GET /metrics"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "component": "log-ingestor"}


@app.get("/ready")
async def ready():
    """Readiness check — verifies Kafka producer is alive."""
    try:
        if kafka is None:
            return Response(status_code=503, content="kafka not initialised")
        return {"status": "ready"}
    except Exception:
        return Response(status_code=503, content="kafka unavailable")


@app.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
