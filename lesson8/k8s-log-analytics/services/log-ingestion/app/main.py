from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import asyncio
import json
from aiokafka import AIOKafkaProducer
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import os
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_RECEIVED = Counter('logs_received_total', 'Total number of logs received')
LOGS_PROCESSED = Counter('logs_processed_total', 'Total number of logs processed')
LOGS_FAILED = Counter('logs_failed_total', 'Total number of failed log processing')
LOG_PROCESSING_TIME = Histogram('log_processing_seconds', 'Time spent processing logs')

app = FastAPI(title="Log Ingestion Service", version="1.0.0")

# Kafka producer (initialized on startup)
kafka_producer: Optional[AIOKafkaProducer] = None

# Redis client for metrics (initialized on startup)
redis_client: Optional[redis.Redis] = None

# In-memory metrics cache (fallback)
metrics_cache: Dict[str, Any] = {
    "services": [],
    "timeSeries": []
}

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('level')
    def validate_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Level must be one of {allowed_levels}')
        return v.upper()

@app.on_event("startup")
async def startup_event():
    """Initialize Kafka producer and Redis on startup"""
    global kafka_producer, redis_client
    kafka_brokers = os.getenv('KAFKA_BROKERS', 'kafka:9092')
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
    
    # Initialize Kafka producer
    try:
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip',
            max_batch_size=16384,
            linger_ms=10
        )
        await kafka_producer.start()
        logger.info(f"Kafka producer started successfully: {kafka_brokers}")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        # Continue without Kafka for local development
        kafka_producer = None
    
    # Initialize Redis client
    try:
        redis_client = await redis.from_url(redis_url)
        await redis_client.ping()
        logger.info(f"Redis connected successfully: {redis_url}")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
        redis_client = None
    
    # Start background task to update metrics
    asyncio.create_task(update_metrics_periodically())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global kafka_producer, redis_client
    if kafka_producer:
        await kafka_producer.stop()
        logger.info("Kafka producer stopped")
    if redis_client:
        await redis_client.close()
        logger.info("Redis client closed")

@app.get("/health")
async def health_check():
    """Liveness probe - checks if service is alive"""
    return {"status": "healthy", "service": "log-ingestion"}

@app.get("/ready")
async def readiness_check():
    """Readiness probe - checks if service can accept traffic"""
    # Service is ready if it can accept HTTP requests, Kafka is optional
    return {"status": "ready", "service": "log-ingestion"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/api/metrics")
async def api_metrics():
    """Dashboard metrics endpoint - returns JSON"""
    try:
        services_data = await get_services_metrics()
        time_series = await get_time_series_data()
        
        return {
            "services": services_data,
            "timeSeries": time_series
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        # Return cached or sample data
        return {
            "services": metrics_cache.get("services", get_sample_services()),
            "timeSeries": metrics_cache.get("timeSeries", get_sample_timeseries())
        }

async def get_services_metrics() -> List[Dict[str, Any]]:
    """Get metrics aggregated by service"""
    if redis_client:
        try:
            # Get active services
            active_services = await redis_client.smembers('active_services')
            services_data = []
            
            for service_bytes in active_services:
                service = service_bytes.decode('utf-8')
                total = 0
                errors = 0
                warnings = 0
                info = 0
                
                # Get counts for each level
                for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG', 'CRITICAL']:
                    count_bytes = await redis_client.hget('log_counts', f"{service}:{level}")
                    if count_bytes:
                        count = int(count_bytes)
                        total += count
                        if level == 'ERROR' or level == 'CRITICAL':
                            errors += count
                        elif level == 'WARNING':
                            warnings += count
                        else:
                            info += count
                
                if total > 0:
                    services_data.append({
                        "service": service,
                        "total": total,
                        "errors": errors,
                        "warnings": warnings,
                        "info": info
                    })
            
            return services_data if services_data else get_sample_services()
        except Exception as e:
            logger.error(f"Redis query failed: {e}")
    
    return get_sample_services()

async def get_time_series_data() -> List[Dict[str, Any]]:
    """Get time series data for charts"""
    # Generate sample time series data
    now = datetime.utcnow()
    time_series = []
    for i in range(50, 0, -1):
        timestamp = now - timedelta(seconds=i*2)
        time_series.append({
            "timestamp": timestamp.strftime("%H:%M:%S"),
            "count": 10 + (i % 20)  # Sample data
        })
    return time_series

def get_sample_services() -> List[Dict[str, Any]]:
    """Return sample service metrics"""
    return [
        {
            "service": "log-ingestion",
            "total": 1250,
            "errors": 15,
            "warnings": 45,
            "info": 1190
        },
        {
            "service": "analytics-engine",
            "total": 980,
            "errors": 8,
            "warnings": 32,
            "info": 940
        },
        {
            "service": "dashboard",
            "total": 320,
            "errors": 2,
            "warnings": 5,
            "info": 313
        }
    ]

def get_sample_timeseries() -> List[Dict[str, Any]]:
    """Return sample time series data"""
    now = datetime.utcnow()
    return [
        {
            "timestamp": (now - timedelta(seconds=i*2)).strftime("%H:%M:%S"),
            "count": 10 + (i % 20)
        }
        for i in range(50, 0, -1)
    ]

async def update_metrics_periodically():
    """Background task to update metrics cache"""
    while True:
        try:
            services = await get_services_metrics()
            time_series = await get_time_series_data()
            metrics_cache["services"] = services
            metrics_cache["timeSeries"] = time_series
            await asyncio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
            await asyncio.sleep(5)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    try:
        while True:
            # Send metrics update every 2 seconds
            services = await get_services_metrics()
            time_series = await get_time_series_data()
            
            # Send metrics update
            await websocket.send_json({
                "type": "metrics",
                "metrics": services
            })
            
            # Send time series point
            if time_series:
                await websocket.send_json({
                    "type": "timeseries",
                    "point": time_series[-1]
                })
            
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

@app.post("/logs")
@LOG_PROCESSING_TIME.time()
async def ingest_log(log: LogEntry, background_tasks: BackgroundTasks):
    """Ingest a single log entry"""
    LOGS_RECEIVED.inc()
    
    try:
        # Convert log to dict
        log_dict = log.dict()
        log_dict['timestamp'] = log_dict['timestamp'].isoformat()
        log_dict['ingestion_timestamp'] = datetime.utcnow().isoformat()
        
        # Send to Kafka asynchronously
        if kafka_producer:
            background_tasks.add_task(send_to_kafka, log_dict)
        
        LOGS_PROCESSED.inc()
        logger.info(f"Log ingested: {log.service} - {log.level}")
        
        return {
            "status": "accepted",
            "timestamp": log_dict['ingestion_timestamp']
        }
    except Exception as e:
        LOGS_FAILED.inc()
        logger.error(f"Failed to process log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def send_to_kafka(log_dict: Dict[str, Any]):
    """Send log to Kafka topic"""
    if not kafka_producer:
        logger.warning("Kafka producer not available, skipping")
        return
    
    try:
        topic = 'logs'
        await kafka_producer.send_and_wait(topic, value=log_dict)
        logger.debug(f"Log sent to Kafka topic: {topic}")
    except Exception as e:
        logger.error(f"Failed to send log to Kafka: {e}")
        LOGS_FAILED.inc()

@app.post("/logs/batch")
async def ingest_logs_batch(logs: list[LogEntry]):
    """Ingest multiple log entries"""
    results = []
    for log in logs:
        try:
            result = await ingest_log(log, BackgroundTasks())
            results.append({"status": "success", "log": log.dict()})
        except Exception as e:
            results.append({"status": "error", "log": log.dict(), "error": str(e)})
    
    return {
        "total": len(logs),
        "processed": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
