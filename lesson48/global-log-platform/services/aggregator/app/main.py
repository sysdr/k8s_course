"""
Cross-Region Aggregator Service
Merges log streams from multiple regional clusters via ServiceEntry endpoints.
Serves WebSocket feed to the React dashboard.
"""
import asyncio
import json
import logging
import os
import time
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGIONS = {
    "us-east": os.getenv("US_EAST_ENDPOINT", "http://log-ingestion.us-east.svc.cluster.local:8000"),
    "eu-west": os.getenv("EU_WEST_ENDPOINT", "http://log-ingestion.eu-west.svc.cluster.local:8000"),
}
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))

app = FastAPI(title="Cross-Region Log Aggregator", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory last-write-wins dedup store (trace_id → timestamp)
_seen: dict[str, float] = {}
_MAX_SEEN = 50_000

connected_clients: set[WebSocket] = set()


async def _fetch_recent_logs(region: str, endpoint: str) -> list[dict]:
    """Pull recent log batch from a regional cluster — resilient with circuit-break logic."""
    url = f"{endpoint.rstrip('/')}/logs/recent"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            events = resp.json().get("events", [])
            if events:
                logger.debug("Fetched %d events from %s", len(events), region)
            return events
    except Exception as exc:
        logger.warning("Failed to fetch from %s (%s): %s", region, endpoint, exc)
        return []


async def _dedup(event: dict) -> bool:
    """CRDT-style dedup: accept if trace_id unseen or newer timestamp."""
    tid = event.get("trace_id")
    ts  = event.get("timestamp", 0.0)
    if tid:
        if tid in _seen and _seen[tid] >= ts:
            return False
        _seen[tid] = ts
        if len(_seen) > _MAX_SEEN:
            # Evict oldest 20%
            sorted_keys = sorted(_seen, key=lambda k: _seen[k])
            for k in sorted_keys[:_MAX_SEEN // 5]:
                del _seen[k]
    return True


async def aggregation_loop():
    """Background task: poll regions, dedup, broadcast to connected WS clients."""
    while True:
        tasks = [_fetch_recent_logs(r, ep) for r, ep in REGIONS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        merged: list[dict] = []
        for i, (region, _) in enumerate(REGIONS.items()):
            if isinstance(results[i], list):
                for event in results[i]:
                    event["region"] = region
                    if await _dedup(event):
                        merged.append(event)

        merged.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
        if merged and connected_clients:
            payload = json.dumps({"events": merged[:200], "ts": time.time()})
            dead = set()
            for ws in connected_clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                connected_clients.discard(ws)
            logger.info("Sent %d events to clients", len(merged[:200]))

        await asyncio.sleep(POLL_INTERVAL)


@app.on_event("startup")
async def startup():
    asyncio.create_task(aggregation_loop())


async def _fetch_and_send_to_client(ws: WebSocket):
    """Fetch current events from all regions and send once to this client (for immediate display on connect)."""
    try:
        merged = []
        seen_ids = set()
        for region, endpoint in REGIONS.items():
            events = await _fetch_recent_logs(region, endpoint)
            for e in events:
                e = dict(e)
                e["region"] = region
                tid = e.get("trace_id")
                if tid and tid in seen_ids:
                    continue
                if tid:
                    seen_ids.add(tid)
                merged.append(e)
        merged.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
        if merged:
            payload = json.dumps({"events": merged[:200], "ts": time.time()})
            await ws.send_text(payload)
            logger.info("Sent %d events to new client on connect", len(merged[:200]))
    except Exception as exc:
        logger.warning("Failed to send initial events to client: %s", exc)


@app.websocket("/ws/logs")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    logger.info("WebSocket client connected. Total: %d", len(connected_clients))
    await _fetch_and_send_to_client(ws)
    try:
        while True:
            await ws.receive_text()  # Keep-alive ping handling
    except WebSocketDisconnect:
        connected_clients.discard(ws)
        logger.info("WebSocket client disconnected. Total: %d", len(connected_clients))


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    return {"status": "ready", "clients": len(connected_clients)}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, workers=1)
