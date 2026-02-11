import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram, generate_latest
from kafka import KafkaProducer
import json
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Ingestor")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# Metrics
REQUEST_COUNT = Counter("log_ingestor_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("log_ingestor_request_duration_seconds", "Latency", ["endpoint"])
ERROR_COUNT = Counter("log_ingestor_errors_total", "Errors", ["type"])

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
producer = None

class LogEntry(BaseModel):
    timestamp: int
    level: str
    service: str
    message: str
    
    @validator("level")
    def validate_level(cls, v):
        if v not in ["DEBUG", "INFO", "WARN", "ERROR"]:
            raise ValueError("Invalid level")
        return v

@app.on_event("startup")
async def startup():
    global producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode()
        )
        logger.info(f"Connected to Kafka: {KAFKA_SERVERS}")
    except Exception as e:
        logger.error(f"Kafka error: {e}")

@app.post("/ingest")
async def ingest(log: LogEntry):
    start = time.time()
    try:
        if not producer:
            raise HTTPException(503, "Kafka unavailable")
        
        producer.send("raw-logs", log.dict())
        REQUEST_COUNT.labels("POST", "/ingest", "200").inc()
        REQUEST_LATENCY.labels("/ingest").observe(time.time() - start)
        return {"status": "success"}
    except Exception as e:
        ERROR_COUNT.labels("ingestion").inc()
        REQUEST_COUNT.labels("POST", "/ingest", "500").inc()
        raise HTTPException(500, str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "kafka": producer is not None}

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
