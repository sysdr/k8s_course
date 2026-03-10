"""Async Kafka producer with connection pooling and retry logic."""
import asyncio
import json
import logging
from typing import Any, Dict

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaTimeoutError

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    def __init__(self, brokers: str, max_retries: int = 3):
        self._brokers = brokers
        self._max_retries = max_retries
        self._producer: AIOKafkaProducer | None = None
        self._connected = False

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            compression_type="snappy",
            max_batch_size=65536,
            linger_ms=5,
            acks="all",
            enable_idempotence=True,
        )
        await self._producer.start()
        self._connected = True
        logger.info("Kafka producer started", extra={"brokers": self._brokers})

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._producer is not None

    async def publish(self, topic: str, key: str, value: Dict[str, Any]) -> None:
        for attempt in range(1, self._max_retries + 1):
            try:
                await self._producer.send_and_wait(topic=topic, key=key, value=value)
                return
            except (KafkaConnectionError, KafkaTimeoutError) as exc:
                if attempt == self._max_retries:
                    logger.error("Kafka publish failed after retries", extra={"attempt": attempt, "error": str(exc)})
                    raise
                await asyncio.sleep(0.1 * (2 ** attempt))
