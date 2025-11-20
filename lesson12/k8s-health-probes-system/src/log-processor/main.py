"""
Log Processor Service - Demonstrates startup probes for slow initialization
and cache warm-up patterns.
"""

import asyncio
import json
import logging
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_PROCESSED = Counter('logs_processed_total', 'Total logs processed')
PROCESSING_ERRORS = Counter('processing_errors_total', 'Processing errors')
PROCESSING_TIME = Histogram('log_processing_duration_seconds', 'Processing duration')
CACHE_HIT_RATE = Gauge('cache_hit_rate', 'Cache hit rate')
MODEL_LOAD_TIME = Gauge('model_load_seconds', 'Time to load ML model')

class AppState:
    def __init__(self):
        self.kafka_consumer: AIOKafkaConsumer | None = None
        self.redis_client: redis.Redis | None = None
        self.is_healthy = False
        self.is_ready = False
        self.startup_complete = False
        self.is_shutting_down = False
        self.model_loaded = False
        self.cache_warmed = False
        self.start_time = time.time()
        self.cache_hits = 0
        self.cache_misses = 0
        # Simulated ML model
        self.classification_model: dict = {}

state = AppState()

class ProcessedLog(BaseModel):
    original: dict
    classification: str
    anomaly_score: float
    processed_at: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    details: dict[str, Any] = {}

async def load_ml_model():
    """
    Simulate loading a large ML model.
    In production, this would load TensorFlow/PyTorch models.
    """
    logger.info("Loading ML classification model...")
    start = time.time()
    
    # Simulate slow model loading (10-20 seconds)
    await asyncio.sleep(random.uniform(10, 20))
    
    # Simulated model weights
    state.classification_model = {
        "weights": [random.random() for _ in range(1000)],
        "categories": ["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"],
        "version": "1.0.0"
    }
    
    load_time = time.time() - start
    MODEL_LOAD_TIME.set(load_time)
    state.model_loaded = True
    logger.info(f"ML model loaded in {load_time:.2f}s")

async def warm_cache():
    """
    Pre-populate cache with frequently accessed data.
    """
    logger.info("Warming cache...")
    
    if not state.redis_client:
        logger.warning("Redis not available, skipping cache warm-up")
        return

    try:
        # Simulate loading historical patterns
        for i in range(100):
            await state.redis_client.set(
                f"pattern:{i}",
                json.dumps({"pattern": f"log_pattern_{i}", "count": random.randint(1, 1000)}),
                ex=3600
            )
        
        # Load classification mappings
        await state.redis_client.hset(
            "classifications",
            mapping={
                "error": "ERROR",
                "warn": "WARNING",
                "info": "INFO",
                "debug": "DEBUG",
                "fatal": "CRITICAL"
            }
        )
        
        state.cache_warmed = True
        logger.info("Cache warm-up complete")
    except Exception as e:
        logger.error(f"Cache warm-up failed: {e}")

async def process_logs():
    """Background task to consume and process logs from Kafka."""
    if not state.kafka_consumer:
        logger.error("Kafka consumer not available")
        return

    try:
        async for msg in state.kafka_consumer:
            if state.is_shutting_down:
                break

            try:
                with PROCESSING_TIME.time():
                    # Parse log
                    log_data = eval(msg.value.decode('utf-8'))
                    
                    # Classify using "ML model"
                    classification = classify_log(log_data)
                    anomaly_score = calculate_anomaly_score(log_data)
                    
                    # Store processed result
                    processed = ProcessedLog(
                        original=log_data,
                        classification=classification,
                        anomaly_score=anomaly_score,
                        processed_at=datetime.utcnow().isoformat()
                    )
                    
                    # Cache result
                    if state.redis_client:
                        await state.redis_client.lpush(
                            "processed_logs",
                            processed.model_dump_json()
                        )
                        await state.redis_client.ltrim("processed_logs", 0, 9999)
                    
                    LOGS_PROCESSED.inc()
                    
            except Exception as e:
                PROCESSING_ERRORS.inc()
                logger.error(f"Error processing log: {e}")
                
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")

def classify_log(log_data: dict) -> str:
    """Classify log using loaded model."""
    if not state.model_loaded:
        return "UNKNOWN"
    
    level = log_data.get("level", "").lower()
    categories = state.classification_model.get("categories", [])
    
    # Simple classification based on level
    level_map = {
        "error": "ERROR",
        "warning": "WARNING",
        "info": "INFO",
        "debug": "DEBUG",
        "critical": "CRITICAL"
    }
    
    return level_map.get(level, random.choice(categories))

def calculate_anomaly_score(log_data: dict) -> float:
    """Calculate anomaly score for log entry."""
    # Simulate anomaly detection
    message = log_data.get("message", "")
    
    # Higher score for certain keywords
    score = 0.1
    if "error" in message.lower():
        score += 0.3
    if "exception" in message.lower():
        score += 0.4
    if "timeout" in message.lower():
        score += 0.2
    
    return min(score, 1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with slow startup handling."""
    logger.info("Starting Log Processor service...")
    
    # Phase 1: Basic initialization (fast)
    state.is_healthy = True
    
    # Phase 2: Load ML model (slow - up to 2 minutes)
    await load_ml_model()
    
    # Phase 3: Connect to dependencies
    try:
        state.redis_client = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True,
            socket_connect_timeout=5
        )
        await state.redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")

    try:
        state.kafka_consumer = AIOKafkaConsumer(
            'logs',
            bootstrap_servers='kafka:9092',
            group_id='log-processor',
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        await state.kafka_consumer.start()
        logger.info("Kafka consumer started")
    except Exception as e:
        logger.error(f"Kafka consumer failed: {e}")

    # Phase 4: Warm cache (triggered by postStart hook)
    await warm_cache()
    
    # Mark startup complete
    state.startup_complete = True
    logger.info("Startup complete")
    
    # Mark ready if all dependencies available
    if state.model_loaded and state.cache_warmed:
        state.is_ready = True
        logger.info("Service is ready")
    
    # Start processing task
    process_task = asyncio.create_task(process_logs())
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    state.is_shutting_down = True
    state.is_ready = False
    
    process_task.cancel()
    try:
        await process_task
    except asyncio.CancelledError:
        pass
    
    if state.kafka_consumer:
        await state.kafka_consumer.stop()
    if state.redis_client:
        await state.redis_client.close()
    
    logger.info("Shutdown complete")

app = FastAPI(
    title="Log Processor Service",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    """
    Liveness probe - only checks internal process health.
    Should NOT check model loading or cache status.
    """
    if not state.is_healthy:
        raise HTTPException(status_code=503, detail="Unhealthy")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        details={
            "uptime_seconds": time.time() - state.start_time
        }
    )

@app.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness probe - checks if service can process logs.
    Requires model loaded and cache warmed.
    """
    if state.is_shutting_down:
        raise HTTPException(status_code=503, detail="Shutting down")
    
    if not state.is_ready:
        raise HTTPException(
            status_code=503,
            detail=f"Not ready: model={state.model_loaded}, cache={state.cache_warmed}"
        )
    
    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        details={
            "model_loaded": state.model_loaded,
            "cache_warmed": state.cache_warmed,
            "logs_processed": LOGS_PROCESSED._value.get()
        }
    )

@app.get("/health/startup", response_model=HealthResponse)
async def startup_check():
    """
    Startup probe - checks if initialization is complete.
    Must succeed before liveness/readiness probes start.
    """
    if state.startup_complete:
        return HealthResponse(
            status="started",
            timestamp=datetime.utcnow().isoformat(),
            details={
                "model_loaded": state.model_loaded,
                "initialization_time": time.time() - state.start_time
            }
        )
    
    raise HTTPException(
        status_code=503,
        detail=f"Still initializing: model_loaded={state.model_loaded}"
    )

@app.post("/cache/warm")
async def trigger_cache_warm():
    """Endpoint for postStart hook to trigger cache warming."""
    if state.cache_warmed:
        return {"status": "already_warmed"}
    
    await warm_cache()
    return {"status": "cache_warmed"}

@app.get("/stats")
async def get_stats():
    """Get processing statistics."""
    return {
        "logs_processed": LOGS_PROCESSED._value.get(),
        "errors": PROCESSING_ERRORS._value.get(),
        "model_version": state.classification_model.get("version", "unknown"),
        "cache_warmed": state.cache_warmed
    }

@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
