"""Log Processor — Kafka consumer + HTTP status / health / metrics."""
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from .consumer import run_consumer
from .database import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","svc":"log-processor","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# ── OTel ──────────────────────────────────────────────────────────────────────
OTLP_ENDPOINT = "http://otel-collector.observability.svc.cluster.local:4317"
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT), export_timeout_millis=1000))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("log-processor")

# ── metrics ───────────────────────────────────────────────────────────────────
MESSAGES_PROCESSED = Counter("log_processor_messages_processed_total", "Messages consumed.", ["service", "severity"])
PROCESS_LATENCY    = Histogram("log_processor_process_latency_seconds", "Per-message processing time.", buckets=[0.001,0.005,0.01,0.05,0.1,0.5,1.0])

shutdown_event = threading.Event()
consumer_thread: threading.Thread | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_thread
    # ensure tables exist (idempotent)
    Base.metadata.create_all(engine)
    consumer_thread = threading.Thread(target=run_consumer, args=(tracer, shutdown_event), daemon=True)
    consumer_thread.start()
    logger.info("Consumer thread started.")
    yield
    shutdown_event.set()
    consumer_thread.join(timeout=10)
    logger.info("Consumer thread stopped.")


app = FastAPI(title="Log Processor", version="1.0.0", lifespan=lifespan)
FastAPIInstrumentor().instrument_app(app)


@app.get("/health")
async def health():
    return {"status": "healthy", "component": "log-processor"}


@app.get("/ready")
async def ready():
    alive = consumer_thread is not None and consumer_thread.is_alive()
    if alive:
        return {"status": "ready"}
    return Response(status_code=503, content="consumer not running")


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/status")
async def status():
    """Light status endpoint for dashboards."""
    return {
        "component": "log-processor",
        "consumer_alive": consumer_thread is not None and consumer_thread.is_alive(),
    }
