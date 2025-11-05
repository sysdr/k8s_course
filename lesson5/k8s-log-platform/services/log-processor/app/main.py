import asyncio
import os
import json
from datetime import datetime
from typing import Optional

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
import redis.asyncio as redis
import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import signal
import sys

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Prometheus metrics
MESSAGES_PROCESSED = Counter('log_processor_messages_processed_total', 'Total messages processed')
PROCESSING_LATENCY = Histogram('log_processor_processing_duration_seconds', 'Processing latency')
DB_WRITE_LATENCY = Histogram('log_processor_db_write_duration_seconds', 'Database write latency')
CACHE_HITS = Counter('log_processor_cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('log_processor_cache_misses_total', 'Cache misses')
KAFKA_LAG = Gauge('log_processor_kafka_lag', 'Kafka consumer lag')

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "application-logs")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "log-processor-group")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql+asyncpg://postgres:password@postgresql:5432/logs")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Database setup
Base = declarative_base()

class LogRecord(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    service = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    log_metadata = Column('metadata', JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)


class LogProcessor:
    def __init__(self):
        self.engine = None
        self.async_session = None
        self.redis_client = None
        self.consumer = None
        self.running = False
        
    async def initialize(self):
        """Initialize database, Redis, and Kafka connections"""
        # Database
        self.engine = create_async_engine(
            POSTGRES_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Redis
        self.redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        
        # Kafka Consumer
        self.consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await self.consumer.start()
        logger.info("processor_initialized")
        
    async def process_message(self, message):
        """Process a single log message"""
        with PROCESSING_LATENCY.time():
            try:
                log_data = message.value
                
                # Enrich log data
                enriched_data = await self.enrich_log(log_data)
                
                # Store in database
                with DB_WRITE_LATENCY.time():
                    async with self.async_session() as session:
                        log_record = LogRecord(
                            level=enriched_data['level'],
                            message=enriched_data['message'],
                            service=enriched_data['service'],
                            timestamp=datetime.fromisoformat(enriched_data['timestamp']) 
                                if isinstance(enriched_data['timestamp'], str) 
                                else enriched_data['timestamp'],
                            log_metadata=enriched_data.get('metadata', {})
                        )
                        session.add(log_record)
                        await session.commit()
                
                # Update cache
                cache_key = f"service:{log_data['service']}:last_log"
                await self.redis_client.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    json.dumps(enriched_data, default=str)
                )
                
                MESSAGES_PROCESSED.inc()
                logger.info(
                    "message_processed",
                    service=log_data['service'],
                    level=log_data['level']
                )
                
            except Exception as e:
                logger.error("message_processing_failed", error=str(e))
                raise
    
    async def enrich_log(self, log_data: dict) -> dict:
        """Enrich log data with additional context"""
        enriched = log_data.copy()
        
        # Check cache for service metadata
        cache_key = f"service:{log_data['service']}:metadata"
        cached_metadata = await self.redis_client.get(cache_key)
        
        if cached_metadata:
            CACHE_HITS.inc()
            service_metadata = json.loads(cached_metadata)
        else:
            CACHE_MISSES.inc()
            # In production, fetch from service registry
            service_metadata = {
                "environment": os.getenv("ENVIRONMENT", "production"),
                "region": os.getenv("REGION", "us-west-2")
            }
            await self.redis_client.setex(cache_key, 7200, json.dumps(service_metadata))
        
        if enriched.get('metadata'):
            enriched['metadata'].update(service_metadata)
        else:
            enriched['metadata'] = service_metadata
        
        return enriched
    
    async def run(self):
        """Main processing loop"""
        self.running = True
        logger.info("processor_started")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                    
                await self.process_message(message)
                
                # Update lag metric
                lag = await self.consumer.highwater() - message.offset
                KAFKA_LAG.set(lag)
                
        except Exception as e:
            logger.error("processor_error", error=str(e))
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("processor_stopping")
        
        if self.consumer:
            await self.consumer.stop()
        
        if self.redis_client:
            await self.redis_client.close()
        
        if self.engine:
            await self.engine.dispose()
        
        logger.info("processor_stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("shutdown_signal_received", signal=signum)
        self.running = False


async def main():
    # Start Prometheus metrics server
    start_http_server(8001)
    
    processor = LogProcessor()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, processor.signal_handler)
    signal.signal(signal.SIGTERM, processor.signal_handler)
    
    await processor.initialize()
    await processor.run()


if __name__ == "__main__":
    asyncio.run(main())
