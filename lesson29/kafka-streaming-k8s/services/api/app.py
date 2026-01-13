import os
import json
import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
from datetime import datetime, timedelta

app = FastAPI(title="Log Analytics API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/stats")
async def get_stats():
    """Get overall statistics"""
    try:
        # Get all stats keys
        stats_keys = redis_client.keys("stats:*")
        
        stats = {}
        for key in stats_keys:
            parts = key.split(':')
            if len(parts) >= 3:
                service = parts[1]
                level = parts[2]
                
                count = redis_client.hget(key, 'count')
                last_seen = redis_client.hget(key, 'last_seen')
                
                if service not in stats:
                    stats[service] = {}
                stats[service][level] = {
                    'count': int(count) if count else 0,
                    'last_seen': last_seen
                }
        
        return stats
    except Exception as e:
        return {"error": str(e)}

@app.get("/logs/{service}")
async def get_logs(service: str, level: Optional[str] = None, limit: int = 100):
    """Get recent logs for a service"""
    try:
        if level:
            key = f"logs:{service}:{level}"
            logs = redis_client.zrevrange(key, 0, limit - 1)
        else:
            # Get from all levels
            all_logs = []
            for lvl in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                key = f"logs:{service}:{lvl}"
                logs = redis_client.zrevrange(key, 0, limit - 1)
                all_logs.extend(logs)
            logs = all_logs[:limit]
        
        return {
            "service": service,
            "level": level,
            "count": len(logs),
            "logs": [json.loads(log) for log in logs]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/alerts/{service}")
async def get_alerts(service: str, limit: int = 50):
    """Get recent alerts for a service"""
    try:
        key = f"alerts:{service}"
        alerts = redis_client.lrange(key, 0, limit - 1)
        
        return {
            "service": service,
            "count": len(alerts),
            "alerts": [json.loads(alert) for alert in alerts]
        }
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live log streaming"""
    await manager.connect(websocket)
    try:
        # Subscribe to Redis pub/sub for real-time updates
        pubsub = redis_client.pubsub()
        pubsub.subscribe('logs-channel')
        
        while True:
            # Send periodic stats updates
            stats = await get_stats()
            await websocket.send_json({"type": "stats", "data": stats})
            
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
