import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from elasticsearch import AsyncElasticsearch
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Sink Service")

# Prometheus metrics
logs_written_total = Counter('logs_written_total', 'Total number of logs written to sink')
write_errors_total = Counter('write_errors_total', 'Total number of write errors')
kafka_connected = Gauge('kafka_connected', 'Kafka connection status (1=connected, 0=disconnected)')
elasticsearch_connected = Gauge('elasticsearch_connected', 'Elasticsearch connection status (1=connected, 0=disconnected)')

class SinkService:
    def __init__(self):
        self.pipeline_name = os.getenv("PIPELINE_NAME", "default")
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")
        self.sink_type = os.getenv("SINK_TYPE", "elasticsearch")
        self.es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
        
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.es_client: Optional[AsyncElasticsearch] = None
        
        self._kafka_connected = False
        self._es_connected = False
        self._kafka_retry_task: Optional[asyncio.Task] = None
        self._es_retry_task: Optional[asyncio.Task] = None
        self._sinking_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def _connect_kafka_with_retry(self):
        """Background task to connect to Kafka with exponential backoff"""
        retry_delay = 1
        max_delay = 60
        
        while not self._shutdown:
            try:
                if self.consumer is None:
                    self.consumer = AIOKafkaConsumer(
                        f"logs-processed-{self.pipeline_name}",
                        bootstrap_servers=self.kafka_brokers,
                        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                        group_id=f"sink-{self.pipeline_name}",
                        request_timeout_ms=5000,
                        retry_backoff_ms=1000
                    )
                
                await self.consumer.start()
                self._kafka_connected = True
                kafka_connected.set(1)
                retry_delay = 1
                logger.info(f"Successfully connected to Kafka at {self.kafka_brokers}")
                
                # Start sinking loop
                if self._sinking_task is None or self._sinking_task.done():
                    self._sinking_task = asyncio.create_task(self.sink_logs())
                
                # Monitor connection
                while not self._shutdown and self._kafka_connected:
                    await asyncio.sleep(30)
                    if self.consumer:
                        await self.consumer.client.bootstrap()
                        
            except (KafkaError, Exception) as e:
                self._kafka_connected = False
                kafka_connected.set(0)
                logger.warning(f"Kafka connection failed: {e}. Retrying in {retry_delay}s...")
                
                if self.consumer:
                    try:
                        await self.consumer.stop()
                    except:
                        pass
                    self.consumer = None
                
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
    
    async def _connect_elasticsearch_with_retry(self):
        """Background task to connect to Elasticsearch with exponential backoff"""
        if self.sink_type != "elasticsearch":
            return
            
        retry_delay = 1
        max_delay = 60
        
        while not self._shutdown:
            try:
                if self.es_client is None:
                    self.es_client = AsyncElasticsearch(
                        [self.es_url],
                        request_timeout=5,
                        max_retries=3
                    )
                
                # Test connection
                await self.es_client.ping()
                self._es_connected = True
                elasticsearch_connected.set(1)
                retry_delay = 1
                logger.info(f"Successfully connected to Elasticsearch at {self.es_url}")
                
                # Monitor connection
                while not self._shutdown and self._es_connected:
                    await asyncio.sleep(30)
                    await self.es_client.ping()
                    
            except Exception as e:
                self._es_connected = False
                elasticsearch_connected.set(0)
                logger.warning(f"Elasticsearch connection failed: {e}. Retrying in {retry_delay}s...")
                
                if self.es_client:
                    try:
                        await self.es_client.close()
                    except:
                        pass
                    self.es_client = None
                
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
    
    async def start(self):
        """Start the sink service (non-blocking)"""
        logger.info(f"Starting sink for pipeline: {self.pipeline_name}")
        self._kafka_retry_task = asyncio.create_task(self._connect_kafka_with_retry())
        if self.sink_type == "elasticsearch":
            self._es_retry_task = asyncio.create_task(self._connect_elasticsearch_with_retry())
    
    async def sink_logs(self):
        """Main log sinking loop"""
        while not self._shutdown and self._kafka_connected:
            try:
                async for msg in self.consumer:
                    if self._shutdown:
                        break
                    try:
                        log_entry = msg.value
                        
                        if self.sink_type == "elasticsearch":
                            await self.write_to_elasticsearch(log_entry)
                        elif self.sink_type == "s3":
                            await self.write_to_s3(log_entry)
                            
                    except Exception as e:
                        logger.error(f"Error sinking log: {e}")
                        write_errors_total.inc()
                        
            except Exception as e:
                logger.error(f"Error in sinking loop: {e}")
                if not self._shutdown:
                    await asyncio.sleep(5)
    
    async def write_to_elasticsearch(self, log: Dict[str, Any]):
        """Write log to Elasticsearch"""
        if not self._es_connected or not self.es_client:
            logger.warning("Elasticsearch not connected, dropping log")
            write_errors_total.inc()
            return
        
        try:
            index_name = f"logs-{self.pipeline_name}"
            await self.es_client.index(
                index=index_name,
                document=log
            )
            logs_written_total.inc()
        except Exception as e:
            logger.error(f"Failed to write to Elasticsearch: {e}")
            write_errors_total.inc()
            self._es_connected = False
            elasticsearch_connected.set(0)
            # Trigger reconnection
            if self._es_retry_task and self._es_retry_task.done():
                self._es_retry_task = asyncio.create_task(self._connect_elasticsearch_with_retry())
    
    async def write_to_s3(self, log: Dict[str, Any]):
        """Write log to S3 (placeholder)"""
        # Implement S3 writing logic
        pass
    
    async def stop(self):
        """Stop the sink"""
        self._shutdown = True
        
        if self._sinking_task:
            self._sinking_task.cancel()
            try:
                await self._sinking_task
            except asyncio.CancelledError:
                pass
        
        if self.consumer:
            try:
                await self.consumer.stop()
            except:
                pass
        
        if self.es_client:
            try:
                await self.es_client.close()
            except:
                pass
        
        if self._kafka_retry_task:
            self._kafka_retry_task.cancel()
            try:
                await self._kafka_retry_task
            except asyncio.CancelledError:
                pass
        
        if self._es_retry_task:
            self._es_retry_task.cancel()
            try:
                await self._es_retry_task
            except asyncio.CancelledError:
                pass

sink = SinkService()

@app.on_event("startup")
async def startup_event():
    """Startup event - never blocks, never fails"""
    try:
        await sink.start()
        logger.info("Sink service started successfully")
    except Exception as e:
        logger.error(f"Error in startup (non-fatal): {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    try:
        await sink.stop()
    except Exception as e:
        logger.error(f"Error in shutdown: {e}")

@app.get("/live")
async def liveness_check():
    """Liveness probe - always returns 200 if process is alive"""
    return {"status": "alive"}

@app.get("/health")
async def health_check():
    """Health check - returns 503 if Kafka not connected"""
    if sink._kafka_connected:
        return {
            "status": "healthy",
            "pipeline": sink.pipeline_name,
            "kafka": "connected" if sink._kafka_connected else "disconnected",
            "elasticsearch": "connected" if sink._es_connected else "disconnected"
        }
    else:
        raise HTTPException(status_code=503, detail="Kafka not connected")

@app.get("/ready")
async def readiness_check():
    """Readiness check - returns 503 if not ready"""
    if sink._kafka_connected:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Not ready")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint - always available"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
