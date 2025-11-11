import asyncio
import json
import os
import re
from datetime import datetime

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from prometheus_client import Counter, start_http_server

Base = declarative_base()

logs_processed = Counter('logs_processed_total', 'Logs processed', ['level'])

class ProcessedLog(Base):
    __tablename__ = 'processed_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    level = Column(String(20), index=True)
    service = Column(String(100), index=True)
    message = Column(Text)
    metadata = Column(JSON)
    parsed_data = Column(JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)

class LogProcessor:
    def __init__(self):
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://loguser:logpass@timescaledb:5432/logsdb")
        
    async def init_db(self):
        self.engine = create_async_engine(self.db_url, echo=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.session_factory = sessionmaker(self.engine, class_=AsyncSession)
        
    async def init_kafka(self):
        self.consumer = AIOKafkaConsumer(
            "logs-raw",
            bootstrap_servers=self.kafka_bootstrap,
            group_id="log-processor",
            value_deserializer=lambda m: json.loads(m.decode())
        )
        await self.consumer.start()
        
    def parse_log(self, message: str) -> dict:
        parsed = {}
        patterns = {
            'user_id': r'user[_-]?id[:\s=]+(\w+)',
            'request_id': r'request[_-]?id[:\s=]+([a-f0-9-]+)',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, message, re.I)
            if match:
                parsed[key] = match.group(1)
        return parsed
        
    async def process_log(self, data: dict) -> ProcessedLog:
        ts = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) if isinstance(data.get('timestamp'), str) else datetime.utcnow()
        
        return ProcessedLog(
            timestamp=ts,
            level=data['level'],
            service=data['service'],
            message=data['message'],
            metadata=data.get('metadata', {}),
            parsed_data=self.parse_log(data['message']),
            processed_at=datetime.utcnow()
        )
        
    async def run(self):
        start_http_server(8001)
        await self.init_db()
        await self.init_kafka()
        
        batch = []
        async for msg in self.consumer:
            try:
                log = await self.process_log(msg.value)
                batch.append(log)
                logs_processed.labels(level=msg.value['level']).inc()
                
                if len(batch) >= 100:
                    async with self.session_factory() as session:
                        session.add_all(batch)
                        await session.commit()
                    batch = []
            except Exception as e:
                print(f"Error: {e}")

async def main():
    processor = LogProcessor()
    await processor.run()

if __name__ == "__main__":
    asyncio.run(main())
