#!/usr/bin/env python3
"""
Log Query Service — REST API over stored log events.
Supports pagination, filtering, full-text search, and aggregations.
"""
import time
from datetime import datetime
from typing import List, Optional

import asyncpg
import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

from config import Settings

settings = Settings()
logger = structlog.get_logger(__name__)

QUERY_TOTAL   = Counter("log_query_requests_total", "Query requests", ["endpoint"])
QUERY_LATENCY = Histogram("log_query_duration_seconds", "Query latency")

app = FastAPI(title="Log Query Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

_pool: asyncpg.Pool | None = None
_redis: aioredis.Redis | None = None


@app.on_event("startup")
async def startup():
    global _pool, _redis
    _pool  = await asyncpg.create_pool(dsn=settings.database_url, min_size=3, max_size=15)
    _redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
    logger.info("query_service.started")


@app.on_event("shutdown")
async def shutdown():
    if _pool:  await _pool.close()
    if _redis: await _redis.aclose()


class LogRecord(BaseModel):
    event_id: str
    service: str
    level: str
    message: str
    timestamp: datetime
    trace_id: Optional[str]


@app.get("/healthz")
async def health():
    try:
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(503, "DB unavailable")


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return PlainTextResponse(generate_latest())


@app.get("/logs", response_model=List[LogRecord])
async def query_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    QUERY_TOTAL.labels(endpoint="logs").inc()
    t0 = time.monotonic()

    filters, args, idx = [], [], 1
    if service:
        filters.append(f"service = ${idx}"); args.append(service); idx += 1
    if level:
        filters.append(f"level = ${idx}"); args.append(level.upper()); idx += 1
    if search:
        filters.append(f"message ILIKE ${idx}"); args.append(f"%{search}%"); idx += 1
    if start:
        filters.append(f"timestamp >= ${idx}"); args.append(start); idx += 1
    if end:
        filters.append(f"timestamp <= ${idx}"); args.append(end); idx += 1

    where = "WHERE " + " AND ".join(filters) if filters else ""
    sql = f"""
        SELECT event_id, service, level, message, timestamp, trace_id
        FROM log_events {where}
        ORDER BY timestamp DESC
        LIMIT ${idx} OFFSET ${idx+1}
    """
    args.extend([limit, offset])

    async with _pool.acquire() as conn:
        rows = await conn.fetch(sql, *args)

    QUERY_LATENCY.observe(time.monotonic() - t0)
    return [dict(r) for r in rows]


@app.get("/logs/stats")
async def log_stats(service: Optional[str] = None):
    QUERY_TOTAL.labels(endpoint="stats").inc()
    cache_key = f"stats:{service or all}"

    cached = await _redis.get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    where = f"WHERE service = $1" if service else ""
    args  = [service] if service else []

    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT level, COUNT(*) as count FROM log_events {where} GROUP BY level",
            *args,
        )

    result = {r["level"]: r["count"] for r in rows}
    import json
    await _redis.setex(cache_key, 30, json.dumps(result))
    return result
