"""
Analytics Service — real-time aggregation layer.

Reads cached counters from Redis, exposes summary endpoints consumed by
the React dashboard via WebSocket fan-out (simplified: polling endpoint here,
WebSocket adapter in the frontend).
"""
import logging
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from .redis_client import TracedRedis

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","svc":"analytics-service","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

OTLP_ENDPOINT = "http://otel-collector.observability.svc.cluster.local:4317"
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT), export_timeout_millis=1000))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("analytics-service")

app = FastAPI(title="Analytics Service", version="1.0.0")
FastAPIInstrumentor().instrument_app(app)

redis = TracedRedis()

# ── metrics ───────────────────────────────────────────────────────────────────
ANALYTICS_REQUESTS = Counter("analytics_requests_total", "Total analytics queries.", ["endpoint"])
QUERY_LATENCY      = Histogram("analytics_query_latency_seconds", "Query latency.", buckets=[0.001,0.005,0.01,0.05,0.1,0.25])

# ── in-memory WebSocket registry ──────────────────────────────────────────────
_ws_clients: list[WebSocket] = []


@app.get("/summary")
async def summary():
    """Return the current aggregation snapshot from Redis."""
    ANALYTICS_REQUESTS.labels(endpoint="summary").inc()
    start = time.perf_counter()

    with tracer.start_as_current_span("redis.read.summary") as span:
        counts_by_severity = redis.hgetall("analytics:counts:severity") or {}
        counts_by_service = redis.hgetall("analytics:counts:service") or {}
        # Convert bytes to strings if needed
        if counts_by_severity:
            counts_by_severity = {k.decode() if isinstance(k, bytes) else k: (v.decode() if isinstance(v, bytes) else v) 
                                for k, v in counts_by_severity.items()}
        if counts_by_service:
            counts_by_service = {k.decode() if isinstance(k, bytes) else k: (v.decode() if isinstance(v, bytes) else v) 
                               for k, v in counts_by_service.items()}
        span.set_attribute("result.severities", len(counts_by_severity))
        span.set_attribute("result.services",   len(counts_by_service))

    QUERY_LATENCY.observe(time.perf_counter() - start)
    return {
        "by_severity": counts_by_severity or {},
        "by_service":  counts_by_service or {},
    }


@app.get("/recent-traces")
async def recent_traces():
    """Return the last N trace IDs seen (stored by the processor via Redis pub)."""
    ANALYTICS_REQUESTS.labels(endpoint="recent-traces").inc()
    with tracer.start_as_current_span("redis.read.traces"):
        # Get trace IDs from Redis list (stored as list, not string)
        trace_ids = redis.lrange("analytics:recent_traces", 0, 49) or []
        # Convert to list of dicts for frontend
        traces = [{"trace_id": tid} for tid in trace_ids]
    return {"traces": traces}


@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    """WebSocket that pushes summary snapshots every 2 seconds."""
    await websocket.accept()
    _ws_clients.append(websocket)
    logger.info("WebSocket client connected")
    try:
        while True:
            try:
                # push current summary - ensure string keys/values for JSON serialization
                severity_data = redis.hgetall("analytics:counts:severity") or {}
                service_data = redis.hgetall("analytics:counts:service") or {}
                # Convert bytes to strings if needed
                if severity_data:
                    severity_data = {k.decode() if isinstance(k, bytes) else k: (v.decode() if isinstance(v, bytes) else v) 
                                   for k, v in severity_data.items()}
                if service_data:
                    service_data = {k.decode() if isinstance(k, bytes) else k: (v.decode() if isinstance(v, bytes) else v) 
                                  for k, v in service_data.items()}
                data = {
                    "by_severity": severity_data or {},
                    "by_service":  service_data or {},
                }
                await websocket.send_json(data)
                # simple sleep; production would use an event loop fan-out
                import asyncio
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}", exc_info=True)
                break
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)


@app.get("/health")
async def health():
    return {"status": "healthy", "component": "analytics-service"}


@app.get("/ready")
async def ready():
    try:
        redis.get("__health__")
        return {"status": "ready"}
    except Exception:
        return Response(status_code=503, content="redis unavailable")


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
