import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import os
from aiokafka import AIOKafkaConsumer
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from prometheus_client import Counter, Gauge, start_http_server
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
LOGS_CONSUMED = Counter('logs_consumed_total', 'Total logs consumed from Kafka')
LOGS_ANALYZED = Counter('logs_analyzed_total', 'Total logs analyzed')
ERROR_LOGS = Counter('error_logs_total', 'Total error logs detected', ['service'])
ACTIVE_SERVICES = Gauge('active_services', 'Number of active services sending logs')

# Database setup
Base = declarative_base()

class LogAnalytics(Base):
    __tablename__ = 'log_analytics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    service = Column(String(100), index=True)
    level = Column(String(20), index=True)
    message = Column(Text)
    metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class AnalyticsEngine:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/logs')
        self.kafka_brokers = os.getenv('KAFKA_BROKERS', 'kafka:9092')
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        
        self.engine = None
        self.Session = None
        self.kafka_consumer = None
        self.redis_client = None
        self.running = False
    
    async def initialize(self):
        """Initialize database and Kafka consumer"""
        try:
            # Database
            self.engine = create_engine(self.db_url, pool_size=10, max_overflow=20)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database initialized")
            
            # Redis
            self.redis_client = await redis.from_url(self.redis_url)
            logger.info("Redis connected")
            
            # Kafka consumer
            self.kafka_consumer = AIOKafkaConsumer(
                'logs',
                bootstrap_servers=self.kafka_brokers,
                group_id='analytics-engine',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            await self.kafka_consumer.start()
            logger.info("Kafka consumer started")
            
            self.running = True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
    
    async def process_logs(self):
        """Main processing loop"""
        logger.info("Starting log processing...")
        
        try:
            async for msg in self.kafka_consumer:
                try:
                    log_data = msg.value
                    await self.analyze_log(log_data)
                    LOGS_CONSUMED.inc()
                    
                except Exception as e:
                    logger.error(f"Error processing log: {e}")
        
        except Exception as e:
            logger.error(f"Processing loop error: {e}")
            self.running = False
    
    async def analyze_log(self, log_data: Dict[str, Any]):
        """Analyze and store log entry"""
        try:
            # Store in database
            session = self.Session()
            try:
                log_entry = LogAnalytics(
                    timestamp=datetime.fromisoformat(log_data['timestamp']),
                    service=log_data['service'],
                    level=log_data['level'],
                    message=log_data['message'],
                    metadata=json.dumps(log_data.get('metadata', {}))
                )
                session.add(log_entry)
                session.commit()
                
                # Update metrics
                LOGS_ANALYZED.inc()
                
                if log_data['level'] in ['ERROR', 'CRITICAL']:
                    ERROR_LOGS.labels(service=log_data['service']).inc()
                
                # Cache aggregated metrics in Redis
                await self.update_redis_metrics(log_data)
                
                logger.debug(f"Analyzed log from {log_data['service']}")
                
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Failed to analyze log: {e}")
    
    async def update_redis_metrics(self, log_data: Dict[str, Any]):
        """Update aggregated metrics in Redis"""
        try:
            service = log_data['service']
            level = log_data['level']
            
            # Increment counters
            await self.redis_client.hincrby('log_counts', f"{service}:{level}", 1)
            
            # Track active services
            await self.redis_client.sadd('active_services', service)
            
            # Update service count gauge
            active_count = await self.redis_client.scard('active_services')
            ACTIVE_SERVICES.set(active_count)
            
        except Exception as e:
            logger.error(f"Redis update failed: {e}")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down analytics engine...")
        self.running = False
        
        if self.kafka_consumer:
            await self.kafka_consumer.stop()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Shutdown complete")

async def main():
    # Start Prometheus metrics server
    start_http_server(8001)
    logger.info("Prometheus metrics available on :8001/metrics")
    
    engine = AnalyticsEngine()
    
    try:
        await engine.initialize()
        await engine.process_logs()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
