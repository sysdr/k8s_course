"""Kafka consumer with Postgres persistence and Redis caching."""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any

import asyncpg
import redis.asyncio as aioredis
from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


class LogConsumer:
    def __init__(self, brokers: str, topic: str, group_id: str, db_dsn: str, redis_url: str):
        self._brokers  = brokers
        self._topic    = topic
        self._group_id = group_id
        self._db_dsn   = db_dsn
        self._redis_url = redis_url
        self._consumer: AIOKafkaConsumer | None = None
        self._pool: asyncpg.Pool | None = None
        self._redis: aioredis.Redis | None = None

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._brokers,
            group_id=self._group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_records=500,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self._consumer.start()
        self._pool  = await asyncpg.create_pool(dsn=self._db_dsn, min_size=5, max_size=20)
        self._redis = await aioredis.from_url(self._redis_url, decode_responses=True)
        logger.info("Consumer started")

    async def stop(self) -> None:
        if self._consumer: await self._consumer.stop()
        if self._pool:     await self._pool.close()
        if self._redis:    await self._redis.aclose()

    async def consume(self) -> AsyncGenerator[Dict[str, Any], None]:
        async for msg in self._consumer:
            yield msg.value
            await self._consumer.commit()

    async def process(self, event: Dict[str, Any]) -> None:
        # Persist to Postgres
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO log_events
                   (event_id, service, level, message, timestamp, trace_id, span_id, metadata)
                   VALUES ($1,$2,$3,$4,to_timestamp($5),$6,$7,$8)
                   ON CONFLICT (event_id) DO NOTHING""",
                event["event_id"],
                event["service"],
                event["level"],
                event["message"],
                event.get("ingested_at", 0),
                event.get("trace_id"),
                event.get("span_id"),
                json.dumps(event.get("metadata", {})),
            )

        # Cache recent error counts per service in Redis (sliding window)
        if event["level"] in ("ERROR", "FATAL"):
            key = f"errors:{event['service']}:1h"
            pipe = self._redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 3600)
            await pipe.execute()
