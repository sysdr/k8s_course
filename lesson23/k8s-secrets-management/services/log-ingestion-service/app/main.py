"""
Log Ingestion Service - Receives logs from external sources
Uses API keys stored in Kubernetes secrets with automatic rotation support
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncio
import json
import os
from datetime import datetime
import aiofiles
import hashlib
from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI(title="Log Ingestion Service", version="1.0.0")

# Prometheus metrics
LOGS_RECEIVED = Counter('logs_received_total', 'Total logs received', ['source', 'status'])
LOG_SIZE = Histogram('log_size_bytes', 'Log entry size in bytes')
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])

# API Key management with hot-reload
API_KEYS = set()
SECRETS_FILE = "/var/run/secrets/api-keys/api-keys"
last_reload_time = None

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str
    service: str
    message: str
    metadata: Optional[dict] = Field(default_factory=dict)
    tenant_id: str

class LogBatch(BaseModel):
    logs: List[LogEntry]
    source: str

async def reload_api_keys():
    """Hot-reload API keys from volume mount"""
    global API_KEYS, last_reload_time
    
    try:
        if os.path.exists(SECRETS_FILE):
            stat = os.stat(SECRETS_FILE)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # Only reload if file has changed
            if last_reload_time is None or mtime > last_reload_time:
                async with aiofiles.open(SECRETS_FILE, 'r') as f:
                    content = await f.read()
                    keys_data = json.loads(content)
                    
                    new_keys = set(keys_data.get('api_keys', []))
                    
                    if new_keys != API_KEYS:
                        API_KEYS.clear()
                        API_KEYS.update(new_keys)
                        last_reload_time = mtime
                        print(f"Reloaded {len(API_KEYS)} API keys at {mtime}")
                        
    except Exception as e:
        print(f"Error reloading API keys: {e}")

@app.on_event("startup")
async def startup():
    """Start API key reload background task"""
    await reload_api_keys()
    asyncio.create_task(api_key_reload_worker())
    print("Log Ingestion Service started")

async def api_key_reload_worker():
    """Background worker to reload API keys periodically"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        await reload_api_keys()

async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from header"""
    if not x_api_key:
        API_REQUESTS.labels(endpoint='ingest', status='missing_key').inc()
        raise HTTPException(status_code=401, detail="API key required")
    
    # Hash key for comparison (in production, use proper crypto)
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    if key_hash not in API_KEYS and x_api_key not in API_KEYS:
        API_REQUESTS.labels(endpoint='ingest', status='invalid_key').inc()
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return x_api_key

@app.post("/api/v1/logs/ingest")
async def ingest_logs(
    log_entry: LogEntry,
    api_key: str = Depends(verify_api_key)
):
    """Ingest single log entry"""
    try:
        # Record metrics
        LOG_SIZE.observe(len(json.dumps(log_entry.dict())))
        LOGS_RECEIVED.labels(source=log_entry.service, status='success').inc()
        API_REQUESTS.labels(endpoint='ingest', status='success').inc()
        
        # In production, send to Kafka/message queue
        # For demo, write to file
        log_data = {
            "timestamp": log_entry.timestamp.isoformat(),
            "level": log_entry.level,
            "service": log_entry.service,
            "message": log_entry.message,
            "tenant_id": log_entry.tenant_id,
            "metadata": log_entry.metadata
        }
        
        print(f"Ingested log: {json.dumps(log_data)}")
        
        return {
            "status": "success",
            "log_id": hashlib.md5(json.dumps(log_data).encode()).hexdigest(),
            "ingested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        LOGS_RECEIVED.labels(source=log_entry.service, status='error').inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/logs/batch")
async def ingest_batch(
    batch: LogBatch,
    api_key: str = Depends(verify_api_key)
):
    """Ingest batch of logs"""
    try:
        ingested_count = 0
        
        for log_entry in batch.logs:
            LOG_SIZE.observe(len(json.dumps(log_entry.dict())))
            LOGS_RECEIVED.labels(source=batch.source, status='success').inc()
            ingested_count += 1
        
        API_REQUESTS.labels(endpoint='batch', status='success').inc()
        
        return {
            "status": "success",
            "ingested_count": ingested_count,
            "batch_id": hashlib.md5(json.dumps(batch.dict()).encode()).hexdigest()
        }
        
    except Exception as e:
        LOGS_RECEIVED.labels(source=batch.source, status='error').inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    # Check if secrets are loaded
    secrets_status = "loaded" if len(API_KEYS) > 0 else "not_loaded"
    
    return {
        "status": "healthy",
        "service": "log-ingestion",
        "secrets_status": secrets_status,
        "api_keys_count": len(API_KEYS)
    }

@app.get("/ready")
async def ready():
    """Readiness check - requires API keys loaded"""
    if len(API_KEYS) == 0:
        raise HTTPException(status_code=503, detail="API keys not loaded")
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest().decode('utf-8')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
