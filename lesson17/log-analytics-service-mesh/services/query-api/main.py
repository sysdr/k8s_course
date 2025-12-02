import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
query_counter = Counter('log_queries_total', 'Total log queries', ['tenant_id', 'query_type'])
query_duration = Histogram('log_query_duration_seconds', 'Time spent executing queries')

# Initialize tracer (optional - only if Jaeger is available)
try:
    jaeger_host = os.getenv('JAEGER_AGENT_HOST', 'jaeger-agent.istio-system.svc.cluster.local')
    jaeger_port = int(os.getenv('JAEGER_AGENT_PORT', '6831'))
    trace.set_tracer_provider(TracerProvider())
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))
    tracer = trace.get_tracer(__name__)
    logger.info(f"Jaeger tracing enabled: {jaeger_host}:{jaeger_port}")
except Exception as e:
    logger.warning(f"Jaeger tracing disabled: {str(e)}")
    tracer = trace.get_tracer(__name__)

# Database setup
Base = declarative_base()

class LogEntry(Base):
    __tablename__ = 'log_entries'
    event_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    service = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    log_metadata = Column('metadata', JSON)
    processed_at = Column(DateTime)

# Pydantic models
class LogEntryResponse(BaseModel):
    event_id: str
    tenant_id: str
    service: str
    severity: str
    message: str
    timestamp: str
    metadata: dict

class StatisticsResponse(BaseModel):
    tenant_id: str
    total_events: int
    events_by_severity: dict
    time_range: dict

# Global resources
db_engine = None
SessionLocal = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_engine, SessionLocal, redis_client
    
    db_host = os.getenv('POSTGRES_HOST', 'timescaledb')
    db_name = os.getenv('POSTGRES_DB', 'logs')
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    redis_host = os.getenv('REDIS_HOST', 'redis')
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
    db_engine = create_engine(db_url, pool_size=10, max_overflow=20)
    SessionLocal = sessionmaker(bind=db_engine)
    
    redis_client = Redis(host=redis_host, port=6379, decode_responses=True)
    
    logger.info("Query API started successfully")
    
    yield
    
    # Shutdown
    if redis_client:
        redis_client.close()
    logger.info("Query API shutdown complete")

app = FastAPI(
    title="Log Query API",
    description="Query API for log analytics platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

@app.get("/api/v1/logs", response_model=List[LogEntryResponse])
async def query_logs(
    tenant_id: str = Query(..., description="Tenant identifier"),
    service: Optional[str] = Query(None, description="Filter by service"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, le=1000, description="Maximum results")
):
    """Query log entries with filters"""
    with tracer.start_as_current_span("query_logs") as span:
        with query_duration.time():
            try:
                span.set_attribute("tenant_id", tenant_id)
                
                session = SessionLocal()
                query = session.query(LogEntry).filter(LogEntry.tenant_id == tenant_id)
                
                if service:
                    query = query.filter(LogEntry.service == service)
                
                if severity:
                    query = query.filter(LogEntry.severity == severity)
                
                if start_time:
                    query = query.filter(LogEntry.timestamp >= datetime.fromisoformat(start_time))
                
                if end_time:
                    query = query.filter(LogEntry.timestamp <= datetime.fromisoformat(end_time))
                
                results = query.order_by(LogEntry.timestamp.desc()).limit(limit).all()
                session.close()
                
                query_counter.labels(tenant_id=tenant_id, query_type='logs').inc()
                
                return [
                    LogEntryResponse(
                        event_id=r.event_id,
                        tenant_id=r.tenant_id,
                        service=r.service,
                        severity=r.severity,
                        message=r.message,
                        timestamp=r.timestamp.isoformat(),
                        metadata=r.log_metadata or {}
                    )
                    for r in results
                ]
                
            except Exception as e:
                logger.error(f"Query failed: {str(e)}", exc_info=True)
                span.record_exception(e)
                raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/api/v1/statistics", response_model=StatisticsResponse)
async def get_statistics(
    tenant_id: str = Query(..., description="Tenant identifier"),
    hours: int = Query(24, description="Time range in hours")
):
    """Get statistics for a tenant"""
    with tracer.start_as_current_span("get_statistics"):
        try:
            session = SessionLocal()
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Total events
            total = session.query(func.count(LogEntry.event_id)).filter(
                LogEntry.tenant_id == tenant_id,
                LogEntry.timestamp >= start_time
            ).scalar()
            
            # Events by severity
            severity_counts = {}
            for severity in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                count = session.query(func.count(LogEntry.event_id)).filter(
                    LogEntry.tenant_id == tenant_id,
                    LogEntry.severity == severity,
                    LogEntry.timestamp >= start_time
                ).scalar()
                severity_counts[severity] = count
            
            session.close()
            
            query_counter.labels(tenant_id=tenant_id, query_type='statistics').inc()
            
            return StatisticsResponse(
                tenant_id=tenant_id,
                total_events=total,
                events_by_severity=severity_counts,
                time_range={
                    'start': start_time.isoformat(),
                    'end': datetime.utcnow().isoformat(),
                    'hours': hours
                }
            )
            
        except Exception as e:
            logger.error(f"Statistics query failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Statistics query failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if db_engine is None:
            raise HTTPException(status_code=503, detail="Database not initialized")
        session = SessionLocal()
        session.execute("SELECT 1")
        session.close()
        if redis_client:
            redis_client.ping()
        return {"status": "healthy", "service": "query-api"}
    except Exception as e:
        logger.warning(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Unhealthy: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.get("/ready")
async def readiness_check():
    """Readiness check"""
    if db_engine is None or redis_client is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}
