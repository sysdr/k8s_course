"""
Analytics API Service - Provides analytics queries and dashboards
Uses multiple secrets: database, external API keys, OAuth tokens
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import json
import os
from datetime import datetime, timedelta
import asyncpg
import aiofiles
import httpx

app = FastAPI(title="Analytics API Service", version="1.0.0")

# Database connection
db_pool = None
db_password = None

# External API credentials
external_api_config = {
    "endpoint": "https://api.example.com",
    "api_key": None
}

# OAuth tokens
oauth_tokens = {}

SECRETS_PATH = "/var/run/secrets"

async def load_all_secrets():
    """Load all secrets from volume mounts"""
    global db_password, oauth_tokens
    
    # Load database credentials
    db_file = f"{SECRETS_PATH}/database/credentials"
    if os.path.exists(db_file):
        async with aiofiles.open(db_file, 'r') as f:
            creds = json.loads(await f.read())
            db_password = creds.get('password')
    
    # Load external API key
    api_file = f"{SECRETS_PATH}/external-api/api-key"
    if os.path.exists(api_file):
        async with aiofiles.open(api_file, 'r') as f:
            api_data = json.loads(await f.read())
            external_api_config['api_key'] = api_data.get('key')
    
    # Load OAuth tokens
    oauth_file = f"{SECRETS_PATH}/oauth/tokens"
    if os.path.exists(oauth_file):
        async with aiofiles.open(oauth_file, 'r') as f:
            oauth_tokens.update(json.loads(await f.read()))

@app.on_event("startup")
async def startup():
    """Initialize service"""
    global db_pool
    
    await load_all_secrets()
    
    # Create database pool
    db_pool = await asyncpg.create_pool(
        host="postgres",
        port=5432,
        database="logs",
        user="loguser",
        password=db_password,
        min_size=5,
        max_size=20
    )
    
    # Start secrets reload worker
    asyncio.create_task(secrets_reload_worker())
    
    print("Analytics API Service started")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

async def secrets_reload_worker():
    """Periodically reload secrets"""
    while True:
        await asyncio.sleep(30)
        try:
            await load_all_secrets()
        except Exception as e:
            print(f"Error reloading secrets: {e}")

@app.get("/api/v1/analytics/tenant/{tenant_id}/summary")
async def get_tenant_summary(tenant_id: str):
    """Get log analytics summary for tenant"""
    try:
        async with db_pool.acquire() as conn:
            # Total logs
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM logs WHERE tenant_id = $1",
                tenant_id
            )
            
            # Logs by level
            by_level = await conn.fetch('''
                SELECT level, COUNT(*) as count 
                FROM logs 
                WHERE tenant_id = $1 
                GROUP BY level
            ''', tenant_id)
            
            # Recent errors
            errors = await conn.fetch('''
                SELECT timestamp, service, message 
                FROM logs 
                WHERE tenant_id = $1 AND level = 'ERROR' 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', tenant_id)
            
            return {
                "tenant_id": tenant_id,
                "total_logs": total,
                "by_level": {row['level']: row['count'] for row in by_level},
                "recent_errors": [
                    {
                        "timestamp": row['timestamp'].isoformat(),
                        "service": row['service'],
                        "message": row['message']
                    }
                    for row in errors
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/external-enrichment")
async def get_external_enrichment():
    """Call external API for data enrichment"""
    if not external_api_config['api_key']:
        raise HTTPException(status_code=503, detail="External API key not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            # Simulated external API call
            response = {
                "status": "success",
                "data": "enriched_data",
                "api_key_used": external_api_config['api_key'][:10] + "..."
            }
            return response
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    secrets_status = {
        "database": "loaded" if db_password else "missing",
        "external_api": "loaded" if external_api_config['api_key'] else "missing",
        "oauth_tokens": "loaded" if oauth_tokens else "missing"
    }
    
    return {
        "status": "healthy",
        "service": "analytics-api",
        "secrets": secrets_status
    }

@app.get("/ready")
async def ready():
    """Readiness check"""
    if not db_password:
        raise HTTPException(status_code=503, detail="Database credentials not loaded")
    
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
