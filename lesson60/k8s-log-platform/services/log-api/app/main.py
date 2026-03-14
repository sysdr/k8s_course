from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import asyncio, logging, os, json
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import aiokafka
import asyncpg
import redis.asyncio as redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
log_requests_total = Counter('log_requests_total', 'Total log ingestion requests', ['status'])
log_ingestion_duration = Histogram('log_ingestion_duration_seconds', 'Log ingestion duration')
kafka_publish_duration = Histogram('kafka_publish_duration_seconds', 'Kafka publish duration')

app = FastAPI(title="Log Ingestion API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-headless:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "logs")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "logdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

kafka_producer = None
db_pool = None
redis_client = None

class LogEntry(BaseModel):
    level: str = Field(..., pattern="^(DEBUG|INFO|WARN|ERROR|FATAL)$")
    message: str
    service: str
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = {}

class LogBatch(BaseModel):
    logs: List[LogEntry]

@app.on_event("startup")
async def startup_event():
    global kafka_producer, db_pool, redis_client
    try:
        kafka_producer = aiokafka.AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, value_serializer=lambda v: json.dumps(v).encode('utf-8'), compression_type='gzip', max_batch_size=32768, linger_ms=10)
        await kafka_producer.start()
        db_pool = await asyncpg.create_pool(host=POSTGRES_HOST, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, min_size=5, max_size=20)
        redis_client = await redis.from_url(f"redis://{REDIS_HOST}", encoding="utf-8", decode_responses=True)
        logger.info("Connections initialized")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global kafka_producer, db_pool, redis_client
    if kafka_producer: await kafka_producer.stop()
    if db_pool: await db_pool.close()
    if redis_client: await redis_client.close()

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    try:
        if not kafka_producer or not getattr(kafka_producer._sender, '_sender_task', None): raise Exception("Kafka not ready")
        async with db_pool.acquire() as conn: await conn.fetchval("SELECT 1")
        await redis_client.ping()
        return {"status": "ready", "kafka": "ok", "postgres": "ok", "redis": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/logs")
async def ingest_log(log_entry: LogEntry, background_tasks: BackgroundTasks):
    with log_ingestion_duration.time():
        try:
            if not log_entry.timestamp:
                log_entry.timestamp = datetime.utcnow()
            log_dict = log_entry.model_dump(mode="json")
            if isinstance(log_dict.get("timestamp"), datetime):
                log_dict["timestamp"] = log_dict["timestamp"].isoformat()
            with kafka_publish_duration.time():
                await kafka_producer.send(KAFKA_TOPIC, value=log_dict)
            cache_key = f"recent_logs:{log_entry.service}"
            await redis_client.lpush(cache_key, json.dumps(log_dict))
            await redis_client.ltrim(cache_key, 0, 99)
            log_requests_total.labels(status='success').inc()
            return {"status": "accepted", "log_id": str(log_dict["timestamp"])}
        except Exception as e:
            log_requests_total.labels(status='error').inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/logs/batch")
async def ingest_batch(log_batch: LogBatch):
    with log_ingestion_duration.time():
        try:
            for log_entry in log_batch.logs:
                if not log_entry.timestamp:
                    log_entry.timestamp = datetime.utcnow()
                log_dict = log_entry.model_dump(mode="json")
                if isinstance(log_dict.get("timestamp"), datetime):
                    log_dict["timestamp"] = log_dict["timestamp"].isoformat()
                await kafka_producer.send(KAFKA_TOPIC, value=log_dict)
            log_requests_total.labels(status='success').inc(len(log_batch.logs))
            return {"status": "accepted", "count": len(log_batch.logs)}
        except Exception as e:
            log_requests_total.labels(status='error').inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/recent/{service}")
async def get_recent_logs(service: str, limit: int = 10):
    try:
        cache_key = f"recent_logs:{service}"
        cached_logs = await redis_client.lrange(cache_key, 0, limit - 1)
        logs = [json.loads(log) for log in cached_logs]
        return {"service": service, "logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/recent")
async def get_all_recent(limit: int = 50):
    try:
        keys = await redis_client.keys("recent_logs:*")
        all_logs = []
        for key in keys[:10]:
            svc = key.replace("recent_logs:", "")
            cached = await redis_client.lrange(key, 0, limit - 1)
            for log in cached:
                try: all_logs.append(json.loads(log))
                except: pass
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return {"service": "all", "logs": all_logs[:limit], "count": len(all_logs[:limit])}
    except Exception as e:
        return {"service": "all", "logs": [], "count": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
