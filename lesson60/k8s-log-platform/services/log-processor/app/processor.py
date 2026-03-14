import asyncio, json, logging, os
from datetime import datetime
import aiokafka, asyncpg
from prometheus_client import Counter, Histogram, start_http_server
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logs_processed_total = Counter("logs_processed_total", "Total logs processed", ["level"])
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-headless:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "logs")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "logdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8001"))
async def main():
    start_http_server(METRICS_PORT)
    consumer = aiokafka.AIOKafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id="log-processor", value_deserializer=lambda m: json.loads(m.decode("utf-8")), auto_offset_reset="earliest")
    await consumer.start()
    db_pool = await asyncpg.create_pool(host=POSTGRES_HOST, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, min_size=2, max_size=10)
    async with db_pool.acquire() as conn:
        await conn.execute("CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, level VARCHAR(10), message TEXT, service VARCHAR(255), timestamp TIMESTAMP, metadata JSONB, created_at TIMESTAMP DEFAULT NOW())")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_service ON logs(service)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC)")
    try:
        async for msg in consumer:
            try:
                d = msg.value
                ts = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
                async with db_pool.acquire() as conn:
                    await conn.execute("INSERT INTO logs (level, message, service, timestamp, metadata) VALUES ($1,$2,$3,$4,$5)", d["level"], d["message"], d["service"], ts, json.dumps(d.get("metadata", {})))
                logs_processed_total.labels(level=d["level"]).inc()
            except Exception as e: logger.error(e)
    finally:
        await consumer.stop()
        await db_pool.close()
if __name__ == "__main__":
    asyncio.run(main())
