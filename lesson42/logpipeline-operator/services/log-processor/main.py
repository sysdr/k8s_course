import asyncio
import logging
import os
import json
import re
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
import redis.asyncio as redis
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Processor Service")

# Prometheus metrics
logs_processed_total = Counter('logs_processed_total', 'Total number of logs processed')
processing_errors_total = Counter('processing_errors_total', 'Total number of processing errors')
kafka_connected = Gauge('kafka_connected', 'Kafka connection status (1=connected, 0=disconnected)')
redis_connected = Gauge('redis_connected', 'Redis connection status (1=connected, 0=disconnected)')

class ProcessorService:
    def __init__(self):
        self.pipeline_name = os.getenv("PIPELINE_NAME", "default")
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")
        self.processors = [p.strip() for p in os.getenv("PROCESSORS", "").split(",") if p.strip()]
        
        # Parse Redis connection - handle both URL format and simple port
        redis_port_str = os.getenv("REDIS_PORT", "6379")
        if "://" in redis_port_str:
            # Extract port from URL like "tcp://10.96.11.42:6379"
            try:
                self.redis_port = int(redis_port_str.split(":")[-1])
            except:
                self.redis_port = 6379
        else:
            self.redis_port = int(redis_port_str)
        
        redis_host_str = os.getenv("REDIS_HOST", "redis")
        if "://" in redis_host_str:
            # Extract host from URL
            self.redis_host = redis_host_str.split("://")[-1].split(":")[0]
        else:
            self.redis_host = redis_host_str
        
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.redis_client: Optional[redis.Redis] = None
        
        self._kafka_connected = False
        self._redis_connected = False
        self._kafka_retry_task: Optional[asyncio.Task] = None
        self._redis_retry_task: Optional[asyncio.Task] = None
        self._processing_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def _connect_kafka_with_retry(self):
        """Background task to connect to Kafka with exponential backoff"""
        retry_delay = 1
        max_delay = 60
        
        while not self._shutdown:
            try:
                if self.consumer is None:
                    self.consumer = AIOKafkaConsumer(
                        f"logs-{self.pipeline_name}",
                        bootstrap_servers=self.kafka_brokers,
                        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                        group_id=f"processor-{self.pipeline_name}",
                        request_timeout_ms=5000,
                        retry_backoff_ms=1000
                    )
                
                if self.producer is None:
                    self.producer = AIOKafkaProducer(
                        bootstrap_servers=self.kafka_brokers,
                        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                        request_timeout_ms=5000,
                        retry_backoff_ms=1000
                    )
                
                await self.consumer.start()
                await self.producer.start()
                self._kafka_connected = True
                kafka_connected.set(1)
                retry_delay = 1
                logger.info(f"Successfully connected to Kafka at {self.kafka_brokers}")
                
                # Start processing loop
                if self._processing_task is None or self._processing_task.done():
                    self._processing_task = asyncio.create_task(self.process_logs())
                
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
                
                if self.producer:
                    try:
                        await self.producer.stop()
                    except:
                        pass
                    self.producer = None
                
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
    
    async def _connect_redis_with_retry(self):
        """Background task to connect to Redis with exponential backoff"""
        retry_delay = 1
        max_delay = 60
        
        while not self._shutdown:
            try:
                if self.redis_client is None:
                    self.redis_client = redis.Redis(
                        host=self.redis_host,
                        port=self.redis_port,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5
                    )
                
                # Test connection
                await self.redis_client.ping()
                self._redis_connected = True
                redis_connected.set(1)
                retry_delay = 1
                logger.info(f"Successfully connected to Redis at {self.redis_host}:{self.redis_port}")
                
                # Monitor connection
                while not self._shutdown and self._redis_connected:
                    await asyncio.sleep(30)
                    await self.redis_client.ping()
                    
            except Exception as e:
                self._redis_connected = False
                redis_connected.set(0)
                logger.warning(f"Redis connection failed: {e}. Retrying in {retry_delay}s...")
                
                if self.redis_client:
                    try:
                        await self.redis_client.close()
                    except:
                        pass
                    self.redis_client = None
                
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
    
    async def start(self):
        """Start the processor service (non-blocking)"""
        logger.info(f"Starting processor for pipeline: {self.pipeline_name}")
        self._kafka_retry_task = asyncio.create_task(self._connect_kafka_with_retry())
        self._redis_retry_task = asyncio.create_task(self._connect_redis_with_retry())
    
    async def process_logs(self):
        """Main log processing loop"""
        while not self._shutdown and self._kafka_connected:
            try:
                async for msg in self.consumer:
                    if self._shutdown:
                        break
                    try:
                        log_entry = msg.value
                        
                        # Apply processors
                        for processor_type in self.processors:
                            if processor_type == "filter":
                                log_entry = await self.filter_log(log_entry)
                            elif processor_type == "parse":
                                log_entry = await self.parse_log(log_entry)
                            elif processor_type == "enrich":
                                log_entry = await self.enrich_log(log_entry)
                            
                            if log_entry is None:
                                break
                        
                        if log_entry:
                            await self.producer.send_and_wait(
                                f"logs-processed-{self.pipeline_name}",
                                log_entry
                            )
                            logs_processed_total.inc()
                            
                    except Exception as e:
                        logger.error(f"Error processing log: {e}")
                        processing_errors_total.inc()
                        
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                if not self._shutdown:
                    await asyncio.sleep(5)  # Brief pause before retry
    
    async def filter_log(self, log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter logs based on level or pattern"""
        if log.get("level") == "DEBUG":
            return None
        return log
    
    async def parse_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Parse log message for structured fields"""
        message = log.get("message", "")
        try:
            json_match = re.search(r'\{.*\}', message)
            if json_match:
                parsed = json.loads(json_match.group())
                log["parsed"] = parsed
        except:
            pass
        return log
    
    async def enrich_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich logs with additional context from Redis cache"""
        if not self._redis_connected or not self.redis_client:
            return log
            
        pod_name = log.get("pod_name")
        if pod_name:
            try:
                cached_data = await self.redis_client.get(f"pod:{pod_name}")
                if cached_data:
                    log["enrichment"] = json.loads(cached_data)
            except Exception as e:
                logger.debug(f"Redis lookup failed: {e}")
        
        return log
    
    async def stop(self):
        """Stop the processor"""
        self._shutdown = True
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        if self.consumer:
            try:
                await self.consumer.stop()
            except:
                pass
        
        if self.producer:
            try:
                await self.producer.stop()
            except:
                pass
        
        if self.redis_client:
            try:
                await self.redis_client.close()
            except:
                pass
        
        if self._kafka_retry_task:
            self._kafka_retry_task.cancel()
            try:
                await self._kafka_retry_task
            except asyncio.CancelledError:
                pass
        
        if self._redis_retry_task:
            self._redis_retry_task.cancel()
            try:
                await self._redis_retry_task
            except asyncio.CancelledError:
                pass

processor = ProcessorService()

@app.on_event("startup")
async def startup_event():
    """Startup event - never blocks, never fails"""
    try:
        await processor.start()
        logger.info("Processor service started successfully")
    except Exception as e:
        logger.error(f"Error in startup (non-fatal): {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    try:
        await processor.stop()
    except Exception as e:
        logger.error(f"Error in shutdown: {e}")

@app.get("/live")
async def liveness_check():
    """Liveness probe - always returns 200 if process is alive"""
    return {"status": "alive"}

@app.get("/health")
async def health_check():
    """Health check - returns 503 if Kafka not connected"""
    if processor._kafka_connected:
        return {
            "status": "healthy",
            "pipeline": processor.pipeline_name,
            "kafka": "connected" if processor._kafka_connected else "disconnected",
            "redis": "connected" if processor._redis_connected else "disconnected"
        }
    else:
        raise HTTPException(status_code=503, detail="Kafka not connected")

@app.get("/ready")
async def readiness_check():
    """Readiness check - returns 503 if not ready"""
    if processor._kafka_connected:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Not ready")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint - always available"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
