"""
Log Processor Service
Consumes from Kafka, persists to PostgreSQL, exposes Prometheus metrics.
"""
import asyncio
import json
import logging
import os
import signal
import time
from typing import Optional

import asyncpg
from aiokafka import AIOKafkaConsumer
from prometheus_client import Counter, Histogram, Gauge, start_http_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC     = os.getenv("KAFKA_TOPIC", "raw-logs")
KAFKA_GROUP     = os.getenv("KAFKA_GROUP_ID", "log-processor-group")
DB_URL          = os.getenv("DATABASE_URL", "postgresql://logs:logs@postgres:5432/logsdb")
REGION          = os.getenv("REGION", "us-east")
BATCH_SIZE      = int(os.getenv("BATCH_SIZE", "100"))
FLUSH_INTERVAL  = float(os.getenv("FLUSH_INTERVAL_SECS", "2.0"))

PROCESSED   = Counter("log_processed_total",    "Processed log events",        ["region", "level"])
DB_ERRORS   = Counter("db_write_errors_total",  "Database write failures",     ["region"])
BATCH_TIME  = Histogram("db_batch_write_seconds","Batch write duration",       ["region"])
QUEUE_DEPTH = Gauge("processor_queue_depth",     "Pending events in buffer",   ["region"])

class LogProcessor:
    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.pool:     Optional[asyncpg.Pool]     = None
        self.buffer:   list = []
        self.running   = True

    async def setup(self):
        logger.info("Connecting to PostgreSQL...")
        self.pool = await asyncpg.create_pool(DB_URL, min_size=2, max_size=10)
        await self._ensure_schema()

        logger.info("Connecting to Kafka consumer group: %s", KAFKA_GROUP)
        self.consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=KAFKA_GROUP,
            value_deserializer=lambda m: json.loads(m.decode()),
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_records=BATCH_SIZE,
        )
        await self.consumer.start()
        logger.info("Consumer started")

    async def _ensure_schema(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS log_events (
                    id          BIGSERIAL PRIMARY KEY,
                    service     TEXT        NOT NULL,
                    level       TEXT        NOT NULL,
                    message     TEXT        NOT NULL,
                    trace_id    TEXT,
                    region      TEXT        NOT NULL,
                    metadata    JSONB       DEFAULT '{}',
                    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_log_events_level   ON log_events(level);
                CREATE INDEX IF NOT EXISTS idx_log_events_service ON log_events(service);
                CREATE INDEX IF NOT EXISTS idx_log_events_ts      ON log_events(ts DESC);
            """)
        logger.info("Schema ensured")

    async def run(self):
        flush_task = asyncio.create_task(self._periodic_flush())
        try:
            async for msg in self.consumer:
                self.buffer.append(msg.value)
                QUEUE_DEPTH.labels(region=REGION).set(len(self.buffer))
                if len(self.buffer) >= BATCH_SIZE:
                    await self._flush()
        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled — flushing remaining buffer")
        finally:
            flush_task.cancel()
            if self.buffer:
                await self._flush()
            await self.consumer.commit()
            await self.consumer.stop()
            await self.pool.close()

    async def _periodic_flush(self):
        while self.running:
            await asyncio.sleep(FLUSH_INTERVAL)
            if self.buffer:
                await self._flush()

    async def _flush(self):
        if not self.buffer:
            return
        batch, self.buffer = self.buffer[:], []
        QUEUE_DEPTH.labels(region=REGION).set(0)
        start = time.perf_counter()
        try:
            async with self.pool.acquire() as conn:
                await conn.executemany(
                    """INSERT INTO log_events (service, level, message, trace_id, region, metadata, ts)
                       VALUES ($1,$2,$3,$4,$5,$6,to_timestamp($7))""",
                    [(e.get("service"), e.get("level"), e.get("message"),
                      e.get("trace_id"), e.get("region", REGION),
                      json.dumps(e.get("metadata", {})),
                      e.get("timestamp")) for e in batch]
                )
            for e in batch:
                PROCESSED.labels(region=REGION, level=e.get("level", "UNKNOWN")).inc()
            elapsed = time.perf_counter() - start
            BATCH_TIME.labels(region=REGION).observe(elapsed)
            logger.info("Flushed %d events in %.3fs", len(batch), elapsed)
        except Exception as exc:
            DB_ERRORS.labels(region=REGION).inc()
            logger.error("Batch write failed: %s — requeueing", exc)
            self.buffer = batch + self.buffer  # requeue

async def main():
    processor = LogProcessor()
    await processor.setup()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(processor.run.__globals__['_shutdown'](processor)))
    start_http_server(9090)
    logger.info("Metrics server on :9090")
    await processor.run()

if __name__ == "__main__":
    asyncio.run(main())
