#!/usr/bin/env python3
"""
Log Processor — Consumes from Kafka, enriches, stores to Postgres + Redis.
"""
import asyncio
import logging
import signal
import time
from contextlib import asynccontextmanager

import structlog
from prometheus_client import Counter, Histogram, start_http_server

from consumer import LogConsumer
from config import Settings

settings = Settings()
logger = structlog.get_logger(__name__)

PROCESSED_TOTAL  = Counter("log_processor_events_total", "Events processed", ["level"])
PROCESSING_LAT   = Histogram("log_processor_duration_seconds", "Processing latency")
PROCESSING_ERRORS = Counter("log_processor_errors_total", "Processing errors")

shutdown_event = asyncio.Event()


async def main() -> None:
    start_http_server(9090)
    logger.info("processor.starting", brokers=settings.kafka_brokers)

    consumer = LogConsumer(
        brokers=settings.kafka_brokers,
        topic=settings.kafka_topic,
        group_id=settings.consumer_group,
        db_dsn=settings.database_url,
        redis_url=settings.redis_url,
    )

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown_event.set())

    await consumer.start()
    logger.info("processor.running")

    async def process_loop():
        async for event in consumer.consume():
            start = time.monotonic()
            try:
                await consumer.process(event)
                PROCESSED_TOTAL.labels(level=event.get("level", "UNKNOWN")).inc()
            except Exception as exc:
                PROCESSING_ERRORS.inc()
                logger.error("event.process_failed", error=str(exc), event_id=event.get("event_id"))
            finally:
                PROCESSING_LAT.observe(time.monotonic() - start)

    process_task = asyncio.create_task(process_loop())
    await shutdown_event.wait()
    process_task.cancel()
    await consumer.stop()
    logger.info("processor.stopped")


if __name__ == "__main__":
    asyncio.run(main())
