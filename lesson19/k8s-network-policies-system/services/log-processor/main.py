"""
Log Processor Service - Consumes from Kafka and stores in TimescaleDB
Network Policy: Accesses data-layer namespace only
"""

import asyncio
import logging
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from prometheus_client import Counter, start_http_server
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
PROCESSED_COUNT = Counter(
    'logs_processed_total',
    'Total logs processed and stored',
    ['level']
)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.data-layer.svc.cluster.local:9092")
KAFKA_TOPIC = "logs"
KAFKA_GROUP_ID = "log-processor-group"

DB_HOST = os.getenv("DB_HOST", "timescaledb.data-layer.svc.cluster.local")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "logs")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def initialize_database():
    """Initialize TimescaleDB tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                level VARCHAR(10) NOT NULL,
                service VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                metadata JSONB,
                ingested_at TIMESTAMPTZ NOT NULL,
                processed_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Create hypertable for time-series optimization
        cur.execute("""
            SELECT create_hypertable('logs', 'timestamp', 
                if_not_exists => TRUE,
                migrate_data => TRUE
            )
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_service ON logs(service)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC)
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def process_messages():
    """Process messages from Kafka and store in database"""
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )
    
    logger.info(f"Starting Kafka consumer for topic: {KAFKA_TOPIC}")
    
    batch = []
    batch_size = 100
    last_commit = time.time()
    
    try:
        for message in consumer:
            try:
                log_data = message.value
                
                # Add to batch
                batch.append((
                    log_data.get('timestamp'),
                    log_data.get('level'),
                    log_data.get('service'),
                    log_data.get('message'),
                    json.dumps(log_data.get('metadata', {})),
                    log_data.get('ingested_at')
                ))
                
                # Process batch if size reached or timeout
                if len(batch) >= batch_size or (time.time() - last_commit) > 5:
                    store_batch(batch)
                    batch = []
                    last_commit = time.time()
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    finally:
        consumer.close()

def store_batch(batch):
    """Store batch of logs in database"""
    if not batch:
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        execute_values(
            cur,
            """
            INSERT INTO logs (timestamp, level, service, message, metadata, ingested_at)
            VALUES %s
            """,
            batch
        )
        conn.commit()
        
        # Update metrics
        for item in batch:
            PROCESSED_COUNT.labels(level=item[1]).inc()
        
        logger.info(f"Stored batch of {len(batch)} logs")
        
    except Exception as e:
        logger.error(f"Failed to store batch: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8002)
    logger.info("Prometheus metrics available on :8002")
    
    # Initialize database
    max_retries = 5
    for i in range(max_retries):
        try:
            initialize_database()
            break
        except Exception as e:
            logger.error(f"Database initialization attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(5)
            else:
                raise
    
    # Start processing
    process_messages()
