"""
Log Processing Service - Processes and stores logs in database
Uses database credentials from Kubernetes secrets with rotation support
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import os
from datetime import datetime
import asyncpg
import aiofiles

app = FastAPI(title="Log Processing Service", version="1.0.0")

# Database connection pool
db_pool = None
db_config = {
    "host": "postgres",
    "port": 5432,
    "database": "logs",
    "user": "loguser",
    "password": None
}

DB_SECRETS_FILE = "/var/run/secrets/database/credentials"
last_password_reload = None

async def reload_db_password():
    """Hot-reload database password from volume mount"""
    global last_password_reload
    
    try:
        if os.path.exists(DB_SECRETS_FILE):
            stat = os.stat(DB_SECRETS_FILE)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            if last_password_reload is None or mtime > last_password_reload:
                async with aiofiles.open(DB_SECRETS_FILE, 'r') as f:
                    content = await f.read()
                    creds = json.loads(content)
                    
                    new_password = creds.get('password')
                    
                    if new_password != db_config['password']:
                        old_password = db_config['password']
                        db_config['password'] = new_password
                        last_password_reload = mtime
                        
                        # Reconnect database pool with new credentials
                        await reconnect_database()
                        
                        print(f"Database password rotated at {mtime}")
                        
    except Exception as e:
        print(f"Error reloading database password: {e}")

async def reconnect_database():
    """Reconnect database pool with new credentials"""
    global db_pool
    
    try:
        # Close existing pool
        if db_pool:
            await db_pool.close()
        
        # Create new pool with updated credentials
        db_pool = await asyncpg.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        print("Database pool reconnected successfully")
        
    except Exception as e:
        print(f"Error reconnecting database: {e}")
        raise

@app.on_event("startup")
async def startup():
    """Initialize database connection"""
    await reload_db_password()
    asyncio.create_task(password_reload_worker())
    
    # Initialize logs table
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                level TEXT NOT NULL,
                service TEXT NOT NULL,
                message TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_logs_tenant ON logs(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
        ''')
    
    print("Log Processing Service started")

@app.on_event("shutdown")
async def shutdown():
    """Close database connections"""
    if db_pool:
        await db_pool.close()

async def password_reload_worker():
    """Background worker to reload database password"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        await reload_db_password()

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str
    tenant_id: str
    metadata: Optional[dict] = {}

@app.post("/api/v1/logs/process")
async def process_log(log: LogEntry):
    """Process and store log entry"""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO logs (timestamp, level, service, message, tenant_id, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', log.timestamp, log.level, log.service, log.message, log.tenant_id, 
                json.dumps(log.metadata))
        
        return {"status": "success", "log_id": "generated-id"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/logs/search")
async def search_logs(
    tenant_id: str,
    level: Optional[str] = None,
    service: Optional[str] = None,
    limit: int = 100
):
    """Search logs"""
    try:
        query = "SELECT * FROM logs WHERE tenant_id = $1"
        params = [tenant_id]
        param_count = 1
        
        if level:
            param_count += 1
            query += f" AND level = ${param_count}"
            params.append(level)
        
        if service:
            param_count += 1
            query += f" AND service = ${param_count}"
            params.append(service)
        
        query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1}"
        params.append(limit)
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return {
            "logs": [
                {
                    "id": row['id'],
                    "timestamp": row['timestamp'].isoformat(),
                    "level": row['level'],
                    "service": row['service'],
                    "message": row['message'],
                    "tenant_id": row['tenant_id'],
                    "metadata": row['metadata']
                }
                for row in rows
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    password_status = "loaded" if db_config['password'] else "not_loaded"
    
    try:
        # Check database connection
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "log-processing",
        "database_password": password_status,
        "database_connection": db_status
    }

@app.get("/ready")
async def ready():
    """Readiness check"""
    if not db_config['password']:
        raise HTTPException(status_code=503, detail="Database password not loaded")
    
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
