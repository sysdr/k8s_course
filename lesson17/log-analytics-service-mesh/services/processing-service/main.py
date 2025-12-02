import os
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any

from kafka import KafkaConsumer
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from redis import Redis
from prometheus_client import Counter, Histogram, start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Prometheus metrics
processing_counter = Counter('log_events_processed_total', 'Total log events processed', ['tenant_id'])
processing_duration = Histogram('log_processing_duration_seconds', 'Time spent processing events')
db_write_duration = Histogram('db_write_duration_seconds', 'Time spent writing to database')

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv('JAEGER_AGENT_HOST', 'jaeger-agent.istio-system.svc.cluster.local'),
    agent_port=int(os.getenv('JAEGER_AGENT_PORT', '6831')),
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))
tracer = trace.get_tracer(__name__)

# Database setup
Base = declarative_base()

class LogEntry(Base):
    __tablename__ = 'log_entries'
    
    event_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    service = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    log_metadata = Column('metadata', JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('idx_severity_timestamp', 'severity', 'timestamp'),
    )

class LogProcessor:
    def __init__(self):
        # Database connection
        db_host = os.getenv('POSTGRES_HOST', 'timescaledb')
        db_name = os.getenv('POSTGRES_DB', 'logs')
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
        self.engine = create_engine(db_url, pool_size=10, max_overflow=20)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Redis connection
        redis_host = os.getenv('REDIS_HOST', 'redis')
        self.redis_client = Redis(host=redis_host, port=6379, decode_responses=True)
        
        # Kafka consumer
        kafka_bootstrap = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        self.consumer = KafkaConsumer(
            'log-events',
            bootstrap_servers=kafka_bootstrap,
            group_id='log-processor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        self.running = True
        logger.info("Log processor initialized successfully")
        
        # Start Prometheus metrics server
        start_http_server(8001)
        logger.info("Prometheus metrics server started on port 8001")
    
    def process_event(self, event: Dict[str, Any]):
        """Process a single log event"""
        with tracer.start_as_current_span("process_event") as span:
            with processing_duration.time():
                try:
                    span.set_attribute("tenant_id", event['tenant_id'])
                    span.set_attribute("event_id", event['event_id'])
                    
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    
                    # Create log entry
                    log_entry = LogEntry(
                        event_id=event['event_id'],
                        tenant_id=event['tenant_id'],
                        service=event['service'],
                        severity=event['severity'],
                        message=event['message'],
                        timestamp=timestamp,
                        log_metadata=event.get('metadata', {})
                    )
                    
                    # Write to database
                    with db_write_duration.time():
                        session = self.Session()
                        try:
                            session.add(log_entry)
                            session.commit()
                        except Exception as e:
                            session.rollback()
                            raise e
                        finally:
                            session.close()
                    
                    # Update Redis cache for statistics
                    cache_key = f"processed_count:{event['tenant_id']}"
                    self.redis_client.incr(cache_key)
                    self.redis_client.expire(cache_key, 3600)
                    
                    # Update severity counters
                    severity_key = f"severity:{event['tenant_id']}:{event['severity']}"
                    self.redis_client.incr(severity_key)
                    self.redis_client.expire(severity_key, 3600)
                    
                    # Update metrics
                    processing_counter.labels(tenant_id=event['tenant_id']).inc()
                    
                    logger.info(
                        "Event processed successfully",
                        extra={
                            'event_id': event['event_id'],
                            'tenant_id': event['tenant_id']
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process event: {str(e)}", exc_info=True)
                    span.record_exception(e)
    
    def run(self):
        """Main processing loop"""
        logger.info("Starting event consumption")
        
        for message in self.consumer:
            if not self.running:
                break
            
            try:
                self.process_event(message.value)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
        
        logger.info("Event consumption stopped")
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down log processor")
        self.running = False
        self.consumer.close()
        self.redis_client.close()
        logger.info("Shutdown complete")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown")
    processor.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    processor = LogProcessor()
    processor.run()
