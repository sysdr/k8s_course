import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from kafka import KafkaProducer
from redis import Redis
from prometheus_client import Counter, Histogram, generate_latest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Prometheus metrics
ingestion_counter = Counter('log_events_ingested_total', 'Total log events ingested', ['tenant_id', 'severity'])
ingestion_duration = Histogram('log_ingestion_duration_seconds', 'Time spent processing ingestion')
kafka_publish_duration = Histogram('kafka_publish_duration_seconds', 'Time spent publishing to Kafka')

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv('JAEGER_AGENT_HOST', 'jaeger-agent.istio-system.svc.cluster.local'),
    agent_port=int(os.getenv('JAEGER_AGENT_PORT', '6831')),
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))
tracer = trace.get_tracer(__name__)

# Global resources
kafka_producer = None
redis_client = None

class LogEvent(BaseModel):
    tenant_id: str = Field(..., description="Tenant identifier")
    service: str = Field(..., description="Service name")
    severity: str = Field(..., description="Log severity level")
    message: str = Field(..., description="Log message")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestionResponse(BaseModel):
    event_id: str
    status: str
    ingested_at: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global kafka_producer, redis_client
    
    kafka_bootstrap = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    redis_host = os.getenv('REDIS_HOST', 'redis')
    
    logger.info(f"Connecting to Kafka: {kafka_bootstrap}")
    kafka_producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )
    
    logger.info(f"Connecting to Redis: {redis_host}")
    redis_client = Redis(host=redis_host, port=6379, decode_responses=True)
    
    logger.info("Ingestion API started successfully")
    
    yield
    
    # Shutdown
    if kafka_producer:
        kafka_producer.close()
    if redis_client:
        redis_client.close()
    logger.info("Ingestion API shutdown complete")

app = FastAPI(
    title="Log Ingestion API",
    description="High-throughput log ingestion service with Kafka backend",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

@app.post("/api/v1/ingest", response_model=IngestionResponse)
async def ingest_log(event: LogEvent):
    """Ingest a single log event"""
    with tracer.start_as_current_span("ingest_log") as span:
        with ingestion_duration.time():
            try:
                span.set_attribute("tenant_id", event.tenant_id)
                span.set_attribute("severity", event.severity)
                
                # Generate event ID
                event_id = f"{event.tenant_id}:{int(datetime.utcnow().timestamp() * 1000000)}"
                
                # Publish to Kafka
                with kafka_publish_duration.time():
                    kafka_producer.send(
                        'log-events',
                        value={
                            'event_id': event_id,
                            'tenant_id': event.tenant_id,
                            'service': event.service,
                            'severity': event.severity,
                            'message': event.message,
                            'timestamp': event.timestamp,
                            'metadata': event.metadata
                        },
                        key=event.tenant_id.encode('utf-8')
                    )
                    kafka_producer.flush()
                
                # Cache recent ingestion count
                cache_key = f"ingestion_count:{event.tenant_id}"
                redis_client.incr(cache_key)
                redis_client.expire(cache_key, 3600)
                
                # Update metrics
                ingestion_counter.labels(tenant_id=event.tenant_id, severity=event.severity).inc()
                
                logger.info(
                    "Log event ingested",
                    extra={
                        'event_id': event_id,
                        'tenant_id': event.tenant_id,
                        'severity': event.severity
                    }
                )
                
                return IngestionResponse(
                    event_id=event_id,
                    status="ingested",
                    ingested_at=datetime.utcnow().isoformat()
                )
                
            except Exception as e:
                logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
                span.record_exception(e)
                raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/v1/ingest/batch", response_model=List[IngestionResponse])
async def ingest_batch(events: List[LogEvent]):
    """Ingest multiple log events in batch"""
    with tracer.start_as_current_span("ingest_batch") as span:
        span.set_attribute("batch_size", len(events))
        
        results = []
        for event in events:
            try:
                result = await ingest_log(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to ingest event: {str(e)}")
                results.append(IngestionResponse(
                    event_id="",
                    status="failed",
                    ingested_at=datetime.utcnow().isoformat()
                ))
        
        return results

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check Kafka connection
        kafka_producer.bootstrap_connected()
        
        # Check Redis connection
        redis_client.ping()
        
        return {"status": "healthy", "service": "ingestion-api"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unhealthy: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    if kafka_producer is None or redis_client is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}
