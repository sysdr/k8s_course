"""
API Service — Lesson 65 Break-It-Friday
This service attempts to call log-processor by DNS name.
In the broken configuration it will fail with connection errors.
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("api-service")

LOG_PROCESSOR_URL = os.getenv("LOG_PROCESSOR_URL", "http://log-processor:8080")


class LogEntry(BaseModel):
    level: str
    message: str
    service: str


class HealthResponse(BaseModel):
    status: str
    upstream_reachable: bool
    upstream_url: str
    latency_ms: float | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"API Service starting. LOG_PROCESSOR_URL={LOG_PROCESSOR_URL}")
    yield
    logger.info("API Service shutting down.")


app = FastAPI(title="API Service", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{LOG_PROCESSOR_URL}/health")
            resp.raise_for_status()
        latency_ms = (time.monotonic() - start) * 1000
        return HealthResponse(
            status="ok",
            upstream_reachable=True,
            upstream_url=LOG_PROCESSOR_URL,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as exc:
        logger.error(f"Upstream health check failed: {exc}")
        return HealthResponse(
            status="degraded",
            upstream_reachable=False,
            upstream_url=LOG_PROCESSOR_URL,
            latency_ms=None,
        )


@app.post("/log")
async def forward_log(entry: LogEntry):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{LOG_PROCESSOR_URL}/ingest",
                json=entry.model_dump(),
            )
            resp.raise_for_status()
        return {"status": "forwarded", "upstream_status": resp.status_code}
    except httpx.ConnectError as exc:
        logger.error(f"DNS/connect failure to {LOG_PROCESSOR_URL}: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot reach log-processor at {LOG_PROCESSOR_URL}. DNS resolution or network failure.",
        )
    except Exception as exc:
        logger.error(f"Unexpected error forwarding log: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
