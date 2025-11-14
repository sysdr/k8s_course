"""
Log Analytics Engine - Stream Processing Service
Consumes log events from Redis streams, aggregates metrics, stores in PostgreSQL.
Demonstrates: init containers, database interactions, stream processing.
"""
import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

import redis.asyncio as redis
import asyncpg
from prometheus_client import Counter, Gauge, start_http_server

# Metrics
logs_processed_counter = Counter('logs_processed_total', 'Total logs processed', ['level', 'service'])
processing_errors_counter = Counter('processing_errors_total', 'Processing errors')
active_streams_gauge = Gauge('active_streams', 'Number of active Redis streams')
db_connection_pool_size = Gauge('db_connection_pool_size', 'Database connection pool size')

# Configuration
REDIS_URL = "redis://redis-service:6379"
POSTGRES_DSN = "postgresql://postgres:postgres@postgres-service:5432/logs"
STREAM_KEY = "logs:stream"
CONSUMER_GROUP = "analytics-workers"
CONSUMER_NAME = "worker-1"

# Global state
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None
shutdown_event = asyncio.Event()

def log_info(msg: str):
    """Structured logging"""
    print(f"[INFO] {datetime.utcnow().isoformat()} - {msg}", flush=True)

def log_error(msg: str):
    """Error logging"""
    print(f"[ERROR] {datetime.utcnow().isoformat()} - {msg}", file=sys.stderr, flush=True)

async def initialize_consumer_group():
    """Create consumer group if it doesn't exist"""
    try:
        await redis_client.xgroup_create(
            name=STREAM_KEY,
            groupname=CONSUMER_GROUP,
            id='0',
            mkstream=True
        )
        log_info(f"Created consumer group: {CONSUMER_GROUP}")
    except redis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            log_info(f"Consumer group {CONSUMER_GROUP} already exists")
        else:
            raise

async def process_log_event(message_id: str, data: Dict[str, str]):
    """Process a single log event and store aggregated metrics"""
    try:
        level = data.get('level', 'UNKNOWN')
        service = data.get('service', 'unknown')
        timestamp = datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
        
        # Aggregate metrics by hour
        hour_bucket = timestamp.replace(minute=0, second=0, microsecond=0)
        
        # Upsert aggregated metrics
        await db_pool.execute("""
            INSERT INTO log_metrics (timestamp, service, level, count, last_updated)
            VALUES ($1, $2, $3, 1, NOW())
            ON CONFLICT (timestamp, service, level)
            DO UPDATE SET 
                count = log_metrics.count + 1,
                last_updated = NOW()
        """, hour_bucket, service, level)
        
        # Update Prometheus metrics
        logs_processed_counter.labels(level=level, service=service).inc()
        
        # Acknowledge message
        await redis_client.xack(STREAM_KEY, CONSUMER_GROUP, message_id)
        
    except Exception as e:
        log_error(f"Error processing message {message_id}: {str(e)}")
        processing_errors_counter.inc()

async def consume_stream():
    """Main stream consumer loop"""
    log_info("Starting stream consumer...")
    
    while not shutdown_event.is_set():
        try:
            # Read from stream
            messages = await redis_client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={STREAM_KEY: '>'},
                count=10,
                block=1000  # 1 second timeout
            )
            
            if messages:
                for stream, stream_messages in messages:
                    active_streams_gauge.set(len(messages))
                    for message_id, data in stream_messages:
                        await process_log_event(message_id, data)
            else:
                active_streams_gauge.set(0)
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            log_info("Consumer cancelled")
            break
        except Exception as e:
            log_error(f"Stream consumption error: {str(e)}")
            processing_errors_counter.inc()
            await asyncio.sleep(5)

async def startup():
    """Initialize connections"""
    global redis_client, db_pool
    
    log_info("Connecting to Redis...")
    redis_client = await redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=10,
        socket_keepalive=True
    )
    
    log_info("Connecting to PostgreSQL...")
    db_pool = await asyncpg.create_pool(
        POSTGRES_DSN,
        min_size=2,
        max_size=10,
        command_timeout=30
    )
    
    # Update pool size metric
    db_connection_pool_size.set(db_pool.get_size())
    
    # Initialize consumer group
    await initialize_consumer_group()
    
    log_info("Startup complete")

async def shutdown():
    """Cleanup connections"""
    log_info("Shutting down gracefully...")
    shutdown_event.set()
    
    if redis_client:
        await redis_client.close()
    if db_pool:
        await db_pool.close()
    
    log_info("Shutdown complete")

def handle_shutdown(signum, frame):
    """Signal handler"""
    log_info(f"Received signal {signum}")
    sys.exit(0)

async def main():
    """Main application loop"""
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    # Start Prometheus metrics server
    start_http_server(8001)
    log_info("Metrics server started on :8001")
    
    try:
        await startup()
        await consume_stream()
    finally:
        await shutdown()

if __name__ == "__main__":
    asyncio.run(main())
