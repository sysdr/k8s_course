"""
Log Processor Service — Lesson 65 Break-It-Friday
Ingests log entries and stores in-memory for local dev.
In the broken stack this service is on backend-net only;
api-service cannot resolve its DNS name or alias.
"""

import logging
import time
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("log-processor")

log_store: deque = deque(maxlen=1000)


class LogEntry(BaseModel):
    level: str
    message: str
    service: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Log Processor starting on port 8080")
    yield
    logger.info("Log Processor shutting down.")


app = FastAPI(title="Log Processor", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "ingested_count": len(log_store)}


@app.post("/ingest")
async def ingest(entry: LogEntry):
    record = {**entry.model_dump(), "timestamp": time.time()}
    log_store.append(record)
    logger.info(f"Ingested: {entry.service} [{entry.level}] {entry.message}")
    return {"status": "ingested", "total": len(log_store)}


@app.get("/logs")
async def get_logs(limit: int = 50):
    entries = list(log_store)[-limit:]
    return {"entries": entries, "total": len(log_store)}
