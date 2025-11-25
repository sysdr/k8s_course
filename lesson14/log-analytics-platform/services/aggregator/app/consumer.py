import asyncio
import asyncpg
import json
import os
import logging
from kafka import KafkaConsumer
from prometheus_client import Counter, Histogram, start_http_server
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
messages_consumed = Counter('messages_consumed_total', 'Total messages consumed from Kafka')
messages_processed = Counter('messages_processed_total', 'Total messages processed successfully')
processing_errors = Counter('processing_errors_total', 'Total processing errors')
processing_duration = Histogram('message_processing_duration_seconds', 'Message processing time')

async def init_database():
    """Initialize database connection"""
    db_host = os.getenv("DB_HOST", "timescaledb-lb.log-analytics.svc.cluster.local")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "logs")
    
    if not db_user or not db_password:
        raise ValueError("DB_USER and DB_PASSWORD environment variables must be set")
    
    pool = await asyncpg.create_pool(
        host=db_host,
        port=5432,
        user=db_user,
        password=db_password,
        database=db_name,
        min_size=2,
        max_size=10
    )
    
    # Ensure table exists
    async with pool.acquire() as conn:
        # Check if table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'logs'
            )
        """)
        
        if not table_exists:
            # Create table without PRIMARY KEY (TimescaleDB requirement for hypertables)
            await conn.execute('''
                CREATE TABLE logs (
                    id SERIAL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    level VARCHAR(10) NOT NULL,
                    message TEXT NOT NULL,
                    source VARCHAR(255) NOT NULL,
                    host VARCHAR(255),
                    metadata JSONB,
                    PRIMARY KEY (id, timestamp)
                );
            ''')
            
            # Convert to hypertable
            await conn.execute("SELECT create_hypertable('logs', 'timestamp', if_not_exists => TRUE);")
            
            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp DESC);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs (level);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_source ON logs (source);')
        else:
            # Table exists, just ensure indexes exist
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp DESC);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs (level);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_source ON logs (source);')
    
    logger.info("Database initialized")
    return pool

async def process_message(pool, message):
    """Process a single message and insert into database"""
    start = datetime.utcnow()
    try:
        log_data = json.loads(message.value.decode('utf-8'))
        
        async with pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO logs (timestamp, level, message, source, host, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', 
                datetime.fromisoformat(log_data['timestamp'].replace('Z', '+00:00')),
                log_data['level'],
                log_data['message'],
                log_data['source'],
                log_data.get('host'),
                json.dumps(log_data.get('metadata', {}))
            )
        
        processing_time = (datetime.utcnow() - start).total_seconds()
        processing_duration.observe(processing_time)
        messages_processed.inc()
        logger.info(f"Processed message from {log_data.get('source', 'unknown')}")
    except Exception as e:
        processing_errors.inc()
        logger.error(f"Failed to process message: {e}")

async def consume_logs():
    """Main consumer loop"""
    # Start Prometheus metrics server
    start_http_server(8002)
    logger.info("Metrics server started on port 8002")
    
    # Initialize database
    pool = await init_database()
    
    # Create Kafka consumer
    consumer = KafkaConsumer(
        'raw-logs',
        bootstrap_servers=['kafka-0.kafka.log-analytics.svc.cluster.local:9092'],
        group_id='log-aggregator',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        max_poll_records=100
    )
    
    logger.info("Kafka consumer started, waiting for messages...")
    
    try:
        batch = []
        batch_size = 10  # Reduced batch size for faster processing
        last_process_time = datetime.utcnow()
        
        for message in consumer:
            messages_consumed.inc()
            batch.append(message)
            
            # Process batch if it reaches batch_size or 5 seconds have passed
            current_time = datetime.utcnow()
            time_since_last_process = (current_time - last_process_time).total_seconds()
            
            if len(batch) >= batch_size or time_since_last_process >= 5:
                if batch:
                    # Process batch
                    await asyncio.gather(*[process_message(pool, msg) for msg in batch])
                    logger.info(f"Processed batch of {len(batch)} messages")
                    batch = []
                    last_process_time = current_time
        
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    finally:
        consumer.close()
        await pool.close()

if __name__ == "__main__":
    asyncio.run(consume_logs())
