import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from kubernetes import client, config, watch
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Collector Service")

# Prometheus metrics
logs_collected_total = Counter('logs_collected_total', 'Total number of logs collected')
kafka_send_errors_total = Counter('kafka_send_errors_total', 'Total number of Kafka send errors')
kafka_connected = Gauge('kafka_connected', 'Kafka connection status (1=connected, 0=disconnected)')

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    pod_name: str
    namespace: str
    container: str
    labels: Dict[str, str] = {}

class CollectorService:
    def __init__(self):
        self.pipeline_name = os.getenv("PIPELINE_NAME", "default")
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")
        self.source_type = os.getenv("SOURCE_TYPE", "kubernetes")
        self.producer: Optional[AIOKafkaProducer] = None
        self._kafka_connected = False
        self._retry_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def _connect_kafka_with_retry(self):
        """Background task to connect to Kafka with exponential backoff"""
        retry_delay = 1  # Start with 1 second
        max_delay = 60  # Max 60 seconds
        
        while not self._shutdown:
            try:
                if self.producer is None:
                    self.producer = AIOKafkaProducer(
                        bootstrap_servers=self.kafka_brokers,
                        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                        request_timeout_ms=5000,
                        retry_backoff_ms=1000
                    )
                
                await self.producer.start()
                self._kafka_connected = True
                kafka_connected.set(1)
                retry_delay = 1  # Reset delay on success
                logger.info(f"Successfully connected to Kafka at {self.kafka_brokers}")
                
                # Start log collection if configured
                if self.source_type == "kubernetes":
                    asyncio.create_task(self.collect_kubernetes_logs())
                
                # Wait and monitor connection
                while not self._shutdown:
                    await asyncio.sleep(30)  # Check connection every 30s
                    if self.producer:
                        # Test connection by getting metadata
                        await self.producer.client.bootstrap()
                        
            except (KafkaError, Exception) as e:
                self._kafka_connected = False
                kafka_connected.set(0)
                logger.warning(f"Kafka connection failed: {e}. Retrying in {retry_delay}s...")
                
                # Clean up failed producer
                if self.producer:
                    try:
                        await self.producer.stop()
                    except:
                        pass
                    self.producer = None
                
                # Exponential backoff
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
    
    async def start(self):
        """Start the collector service (non-blocking)"""
        logger.info(f"Starting collector for pipeline: {self.pipeline_name}")
        # Start background retry task - never blocks startup
        self._retry_task = asyncio.create_task(self._connect_kafka_with_retry())
    
    async def collect_kubernetes_logs(self):
        """Collect logs from Kubernetes pods"""
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        logger.info("Starting Kubernetes log collection")
        # In production, implement proper log tailing
        
    async def send_log(self, log_entry: Dict[str, Any]):
        """Send log entry to Kafka (non-blocking, handles failures gracefully)"""
        if not self._kafka_connected or not self.producer:
            logger.warning("Kafka not connected, dropping log entry")
            kafka_send_errors_total.inc()
            return
        
        try:
            topic = f"logs-{self.pipeline_name}"
            await self.producer.send_and_wait(topic, log_entry)
            logs_collected_total.inc()
        except Exception as e:
            logger.error(f"Failed to send log to Kafka: {e}")
            kafka_send_errors_total.inc()
            self._kafka_connected = False
            kafka_connected.set(0)
            # Trigger reconnection
            if self._retry_task and self._retry_task.done():
                self._retry_task = asyncio.create_task(self._connect_kafka_with_retry())
    
    async def stop(self):
        """Stop the collector"""
        self._shutdown = True
        if self.producer:
            try:
                await self.producer.stop()
            except Exception as e:
                logger.error(f"Error stopping producer: {e}")
        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass

collector = CollectorService()

@app.on_event("startup")
async def startup_event():
    """Startup event - never blocks, never fails"""
    try:
        await collector.start()
        logger.info("Collector service started successfully")
    except Exception as e:
        logger.error(f"Error in startup (non-fatal): {e}")
        # Service continues running

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    try:
        await collector.stop()
    except Exception as e:
        logger.error(f"Error in shutdown: {e}")

@app.get("/live")
async def liveness_check():
    """Liveness probe - always returns 200 if process is alive"""
    return {"status": "alive"}

@app.get("/health")
async def health_check():
    """Health check - returns 503 if Kafka not connected"""
    if collector._kafka_connected:
        return {"status": "healthy", "pipeline": collector.pipeline_name, "kafka": "connected"}
    else:
        raise HTTPException(status_code=503, detail="Kafka not connected")

@app.get("/ready")
async def readiness_check():
    """Readiness check - returns 503 if not ready"""
    if collector._kafka_connected:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Not ready")

@app.post("/logs")
async def ingest_log(log: LogEntry):
    """Ingest a log entry"""
    try:
        await collector.send_log(log.dict())
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Error ingesting log: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint - always available"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
