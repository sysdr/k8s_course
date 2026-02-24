"""
Cross-Cluster Log Processor Service
Consumes logs from Kafka and processes/aggregates them
Demonstrates cross-cluster communication by querying Cluster A
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
import asyncpg
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import httpx
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
PROCESSED_LOGS = Counter('logs_processed_total', 'Total logs processed', ['level', 'service'])
PROCESSING_LATENCY = Histogram('log_processing_latency_seconds', 'Log processing latency')
CROSS_CLUSTER_CALLS = Counter('cross_cluster_calls_total', 'Cross-cluster API calls', ['status'])
ACTIVE_CONSUMERS = Gauge('kafka_active_consumers', 'Number of active Kafka consumers')

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'logs')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'log-processor-group')
POSTGRES_DSN = os.getenv('POSTGRES_DSN', 'postgresql://postgres:postgres@postgres:5432/logs')
CLUSTER_A_URL = os.getenv('CLUSTER_A_URL', 'http://log-ingestion-lb:8000')
CLUSTER_ID = os.getenv('CLUSTER_ID', 'cluster-b')

# Global resources
kafka_consumer: Optional[AIOKafkaConsumer] = None
db_pool: Optional[asyncpg.Pool] = None
processing_task: Optional[asyncio.Task] = None
http_client: Optional[httpx.AsyncClient] = None


class HealthResponse(BaseModel):
    status: str
    cluster_id: str
    kafka_connected: bool
    database_connected: bool
    cluster_a_reachable: bool
    processed_count: int
    timestamp: datetime


class LogStats(BaseModel):
    service: str
    total_logs: int
    error_count: int
    warning_count: int
    last_updated: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global kafka_consumer, db_pool, processing_task, http_client
    
    # Startup
    logger.info(f"Starting Log Processor Service in {CLUSTER_ID}")
    
    try:
        # Initialize database pool
        db_pool = await asyncpg.create_pool(
            POSTGRES_DSN,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database pool created")
        
        # Create tables
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS log_stats (
                    service VARCHAR(100) PRIMARY KEY,
                    total_logs INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    warning_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT NOW()
                )
            ''')
        logger.info("Database schema initialized")
        
        # Initialize Kafka consumer
        kafka_consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            session_timeout_ms=30000
        )
        await kafka_consumer.start()
        logger.info("Kafka consumer started")
        ACTIVE_CONSUMERS.set(1)
        
        # Initialize HTTP client for cross-cluster calls
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=50)
        )
        logger.info("HTTP client initialized")
        
        # Start background processing task
        processing_task = asyncio.create_task(process_logs())
        logger.info("Background processing started")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Log Processor Service")
    
    if processing_task:
        processing_task.cancel()
        try:
            await processing_task
        except asyncio.CancelledError:
            pass
    
    if kafka_consumer:
        await kafka_consumer.stop()
        ACTIVE_CONSUMERS.set(0)
    
    if db_pool:
        await db_pool.close()
    
    if http_client:
        await http_client.aclose()


app = FastAPI(
    title="Cross-Cluster Log Processor API",
    description="Processes logs from Kafka with cross-cluster communication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_logs():
    """Background task to consume and process logs from Kafka"""
    logger.info("Starting log processing loop")
    
    try:
        async for message in kafka_consumer:
            with PROCESSING_LATENCY.time():
                try:
                    log_data = message.value
                    
                    # Extract log details
                    service = log_data.get('service', 'unknown')
                    level = log_data.get('level', 'INFO')
                    
                    # Update statistics in database
                    async with db_pool.acquire() as conn:
                        await conn.execute('''
                            INSERT INTO log_stats (service, total_logs, error_count, warning_count, last_updated)
                            VALUES ($1, 1, $2, $3, NOW())
                            ON CONFLICT (service) 
                            DO UPDATE SET
                                total_logs = log_stats.total_logs + 1,
                                error_count = log_stats.error_count + $2,
                                warning_count = log_stats.warning_count + $3,
                                last_updated = NOW()
                        ''', service, 1 if level == 'ERROR' else 0, 1 if level == 'WARNING' else 0)
                    
                    # Increment Prometheus metrics
                    PROCESSED_LOGS.labels(level=level, service=service).inc()
                    
                    logger.debug(f"Processed log from {service}: {level}")
                    
                except Exception as e:
                    logger.error(f"Error processing log: {e}")
                    
    except asyncio.CancelledError:
        logger.info("Processing loop cancelled")
    except Exception as e:
        logger.error(f"Processing loop error: {e}")


async def check_cluster_a_health() -> bool:
    """Check if Cluster A is reachable (cross-cluster health check)"""
    try:
        response = await http_client.get(f"{CLUSTER_A_URL}/health", timeout=5.0)
        CROSS_CLUSTER_CALLS.labels(status='success').inc()
        return response.status_code == 200
    except Exception as e:
        CROSS_CLUSTER_CALLS.labels(status='error').inc()
        logger.warning(f"Cluster A health check failed: {e}")
        return False


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    kafka_healthy = kafka_consumer is not None
    db_healthy = db_pool is not None
    
    # Test database connection
    if db_healthy:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
        except Exception:
            db_healthy = False
    
    # Check cross-cluster connectivity
    cluster_a_healthy = await check_cluster_a_health()
    
    # Get processed count
    processed_count = 0
    if db_healthy:
        try:
            async with db_pool.acquire() as conn:
                processed_count = await conn.fetchval('SELECT COALESCE(SUM(total_logs), 0) FROM log_stats')
        except Exception:
            pass
    
    status_code = "healthy" if (kafka_healthy and db_healthy) else "degraded"
    
    return HealthResponse(
        status=status_code,
        cluster_id=CLUSTER_ID,
        kafka_connected=kafka_healthy,
        database_connected=db_healthy,
        cluster_a_reachable=cluster_a_healthy,
        processed_count=processed_count or 0,
        timestamp=datetime.utcnow()
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    if not kafka_consumer or not db_pool:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    return {"status": "ready"}


@app.get("/stats", response_model=List[LogStats])
async def get_stats():
    """Get aggregated log statistics"""
    if not db_pool:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT service, total_logs, error_count, warning_count, last_updated FROM log_stats ORDER BY total_logs DESC'
            )
            
            return [
                LogStats(
                    service=row['service'],
                    total_logs=row['total_logs'],
                    error_count=row['error_count'],
                    warning_count=row['warning_count'],
                    last_updated=row['last_updated']
                )
                for row in rows
            ]
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stats"
        )


@app.get("/stats/cluster-a")
async def get_cluster_a_stats():
    """
    Cross-cluster communication example
    Queries Cluster A's stats endpoint to demonstrate multi-cluster interaction
    """
    try:
        response = await http_client.get(f"{CLUSTER_A_URL}/stats", timeout=10.0)
        CROSS_CLUSTER_CALLS.labels(status='success').inc()
        
        if response.status_code == 200:
            return {
                "source": "cluster-a",
                "data": response.json(),
                "retrieved_at": datetime.utcnow().isoformat()
            }
        else:
            CROSS_CLUSTER_CALLS.labels(status='error').inc()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cluster A returned status {response.status_code}"
            )
    except httpx.TimeoutException:
        CROSS_CLUSTER_CALLS.labels(status='timeout').inc()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Cluster A request timeout"
        )
    except Exception as e:
        CROSS_CLUSTER_CALLS.labels(status='error').inc()
        logger.error(f"Cross-cluster request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to communicate with Cluster A"
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
