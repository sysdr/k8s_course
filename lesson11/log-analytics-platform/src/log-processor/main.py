import os
import json
import asyncio
import logging
import yaml
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Load configuration from ConfigMap volume mount
def load_config():
    config_path = Path("/etc/config/config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            file_config = yaml.safe_load(f)
    else:
        file_config = {}
    
    return {
        "log_level": os.getenv("LOG_LEVEL", "info"),
        "kafka_brokers": os.getenv("KAFKA_BROKERS", "kafka:9092"),
        "kafka_topic": os.getenv("KAFKA_TOPIC", "raw-logs"),
        "kafka_group": os.getenv("KAFKA_GROUP", "log-processor"),
        "db_host": os.getenv("DB_HOST", "postgres"),
        "db_port": os.getenv("DB_PORT", "5432"),
        "db_name": os.getenv("DB_NAME", "logs"),
        "db_user": os.getenv("DB_USER", "log_processor"),
        "db_password": os.getenv("DB_PASSWORD", ""),
        "redis_host": os.getenv("REDIS_HOST", "redis"),
        "redis_password": os.getenv("REDIS_PASSWORD", ""),
        "workers": file_config.get("processing", {}).get("workers", 4),
        "batch_size": file_config.get("processing", {}).get("batch_size", 100),
        "timeout_ms": file_config.get("processing", {}).get("timeout_ms", 5000),
        "async_writes": file_config.get("features", {}).get("async_writes", True),
    }

CONFIG = load_config()

# Logging
logging.basicConfig(
    level=getattr(logging, CONFIG["log_level"].upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_PROCESSED = Counter('logs_processed_total', 'Total logs processed', ['status'])
PROCESSING_LAG = Gauge('processing_lag_seconds', 'Kafka consumer lag in seconds')
BATCH_SIZE = Histogram('batch_size', 'Size of processed batches')
DB_WRITES = Counter('db_writes_total', 'Total database writes', ['status'])

# Global clients
consumer: Optional[KafkaConsumer] = None
redis_client: Optional[redis.Redis] = None
db_engine = None
processing_task = None

async def get_db_session():
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

async def process_logs():
    """Background task to consume and process logs from Kafka"""
    global consumer
    
    while True:
        try:
            messages = consumer.poll(timeout_ms=CONFIG["timeout_ms"], max_records=CONFIG["batch_size"])
            
            if not messages:
                await asyncio.sleep(0.1)
                continue
            
            batch = []
            for tp, records in messages.items():
                for record in records:
                    try:
                        log_data = record.value
                        # Enrich log
                        log_data['processed_at'] = datetime.utcnow().isoformat()
                        log_data['partition'] = record.partition
                        log_data['offset'] = record.offset
                        # Ensure timestamp field exists (use ingested_at if timestamp is missing)
                        if 'timestamp' not in log_data and 'ingested_at' in log_data:
                            log_data['timestamp'] = log_data['ingested_at']
                        elif 'timestamp' not in log_data:
                            log_data['timestamp'] = datetime.utcnow().isoformat()
                        batch.append(log_data)
                    except Exception as e:
                        logger.error(f"Failed to process record: {e}")
                        LOGS_PROCESSED.labels(status='failed').inc()
            
            if batch:
                BATCH_SIZE.observe(len(batch))
                
                # Write to database
                async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
                async with async_session() as session:
                    try:
                        for log in batch:
                            await session.execute(
                                text("""
                                    INSERT INTO logs (timestamp, level, service, message, metadata, trace_id)
                                    VALUES (:timestamp, :level, :service, :message, :metadata, :trace_id)
                                """),
                                {
                                    "timestamp": datetime.fromisoformat(log.get("timestamp", log.get("ingested_at", datetime.utcnow().isoformat()))),
                                    "level": log.get("level"),
                                    "service": log.get("service"),
                                    "message": log.get("message"),
                                    "metadata": json.dumps(log.get("metadata", {})),
                                    "trace_id": log.get("trace_id")
                                }
                            )
                        await session.commit()
                        DB_WRITES.labels(status='success').inc(len(batch))
                        LOGS_PROCESSED.labels(status='success').inc(len(batch))
                    except Exception as e:
                        logger.error(f"Database write failed: {e}")
                        await session.rollback()
                        DB_WRITES.labels(status='failed').inc(len(batch))
                        LOGS_PROCESSED.labels(status='failed').inc(len(batch))
                
                # Update Redis cache
                for log in batch:
                    redis_client.zadd(
                        f"recent_logs:{log['service']}",
                        {json.dumps(log): datetime.utcnow().timestamp()}
                    )
                    # Keep only last 1000 logs per service
                    redis_client.zremrangebyrank(f"recent_logs:{log['service']}", 0, -1001)
                
                consumer.commit()
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer, redis_client, db_engine, processing_task
    
    # Initialize database
    db_url = f"postgresql+asyncpg://{CONFIG['db_user']}:{CONFIG['db_password']}@{CONFIG['db_host']}:{CONFIG['db_port']}/{CONFIG['db_name']}"
    db_engine = create_async_engine(db_url, pool_size=10, max_overflow=20)
    
    # Create table if not exists
    async with db_engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ,
                level VARCHAR(10),
                service VARCHAR(100),
                message TEXT,
                metadata JSONB,
                trace_id VARCHAR(100),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_service ON logs(service)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)"))
    
    logger.info("Database initialized")
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        CONFIG["kafka_topic"],
        bootstrap_servers=CONFIG["kafka_brokers"].split(","),
        group_id=CONFIG["kafka_group"],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=False
    )
    logger.info(f"Connected to Kafka topic {CONFIG['kafka_topic']}")
    
    # Initialize Redis
    redis_client = redis.Redis(
        host=CONFIG["redis_host"],
        password=CONFIG["redis_password"] or None,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Connected to Redis")
    
    # Start processing task
    processing_task = asyncio.create_task(process_logs())
    
    yield
    
    # Cleanup
    processing_task.cancel()
    consumer.close()
    redis_client.close()
    await db_engine.dispose()

app = FastAPI(
    title="Log Processor Service",
    description="Processes logs from Kafka and stores in PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "log-processor"}

@app.get("/ready")
async def readiness_check():
    try:
        redis_client.ping()
        async with db_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/config")
async def get_config():
    """Return current configuration (excluding secrets)"""
    safe_config = {k: v for k, v in CONFIG.items() if 'password' not in k.lower()}
    return safe_config

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
