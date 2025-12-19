"""
Vault Simulator - Educational HashiCorp Vault implementation
Simulates vault key-value secret store with rotation capabilities
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
import asyncio
import secrets
import hashlib
import json
from datetime import datetime, timedelta
import asyncpg
import os

app = FastAPI(title="Vault Simulator", version="1.0.0")

# Database connection pool
db_pool = None

# Vault authentication tokens (in production, use proper JWT/OAuth)
VALID_TOKENS = set()

class SecretData(BaseModel):
    key: str
    value: str
    metadata: Optional[Dict] = Field(default_factory=dict)

class SecretResponse(BaseModel):
    request_id: str
    data: Dict
    metadata: Dict
    lease_duration: int = 3600
    renewable: bool = True

class RotationConfig(BaseModel):
    enabled: bool = True
    rotation_interval: int = 300  # 5 minutes for demo
    grace_period: int = 90  # Old secret valid for 90 seconds

@app.on_event("startup")
async def startup():
    """Initialize database connection pool"""
    global db_pool
    # Construct DATABASE_URL from individual env vars or use DATABASE_URL if provided
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        postgres_user = os.getenv("POSTGRES_USER", "postgres")
        postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        postgres_host = os.getenv("POSTGRES_HOST", "postgres")
        postgres_port = os.getenv("POSTGRES_PORT", "5432")
        postgres_db = os.getenv("POSTGRES_DB", "vault")
        db_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    db_pool = await asyncpg.create_pool(
        db_url,
        min_size=5,
        max_size=20,
        command_timeout=60
    )
    
    # Initialize secrets table
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS secrets (
                path TEXT PRIMARY KEY,
                data JSONB NOT NULL,
                metadata JSONB DEFAULT '{}',
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rotation_enabled BOOLEAN DEFAULT TRUE,
                last_rotated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                operation TEXT NOT NULL,
                path TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                metadata JSONB DEFAULT '{}'
            )
        ''')
    
    # Initialize demo token for development (if provided via environment variable)
    demo_token = os.getenv("VAULT_DEMO_TOKEN")
    if demo_token:
        VALID_TOKENS.add(demo_token)
    
    # Start secret rotation background task
    asyncio.create_task(rotation_worker())
    
    print("Vault Simulator started successfully")

@app.on_event("shutdown")
async def shutdown():
    """Close database connections"""
    if db_pool:
        await db_pool.close()

def hash_token(token: str) -> str:
    """Hash token for audit logging"""
    return hashlib.sha256(token.encode()).hexdigest()[:16]

async def verify_token(x_vault_token: str = Header(...)) -> str:
    """Verify vault token (simplified auth)"""
    if not x_vault_token or x_vault_token not in VALID_TOKENS:
        raise HTTPException(status_code=403, detail="Invalid token")
    return x_vault_token

@app.post("/v1/auth/token/create")
async def create_token():
    """Create new vault token"""
    token = f"hvs.{secrets.token_urlsafe(32)}"
    VALID_TOKENS.add(token)
    return {"auth": {"client_token": token, "lease_duration": 3600}}

@app.get("/v1/secret/data/{path:path}")
async def read_secret(path: str, token: str = Depends(verify_token)):
    """Read secret from vault"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT data, metadata, version FROM secrets WHERE path = $1",
            path
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Secret not found")
        
        # Log access
        await conn.execute(
            "INSERT INTO audit_log (operation, path, token_hash) VALUES ($1, $2, $3)",
            "read", path, hash_token(token)
        )
        
        return SecretResponse(
            request_id=secrets.token_hex(16),
            data={"data": row['data'], "metadata": row['metadata']},
            metadata={"version": row['version'], "created_time": "2024-01-01T00:00:00Z"}
        )

@app.post("/v1/secret/data/{path:path}")
async def write_secret(
    path: str, 
    secret: SecretData,
    token: str = Depends(verify_token)
):
    """Write secret to vault"""
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO secrets (path, data, metadata)
            VALUES ($1, $2, $3)
            ON CONFLICT (path) 
            DO UPDATE SET 
                data = $2,
                metadata = $3,
                version = secrets.version + 1,
                updated_at = CURRENT_TIMESTAMP
        ''', path, json.dumps({secret.key: secret.value}), json.dumps(secret.metadata))
        
        # Log write
        await conn.execute(
            "INSERT INTO audit_log (operation, path, token_hash, metadata) VALUES ($1, $2, $3, $4)",
            "write", path, hash_token(token), json.dumps({"key": secret.key})
        )
        
        return {"request_id": secrets.token_hex(16), "success": True}

@app.delete("/v1/secret/data/{path:path}")
async def delete_secret(path: str, token: str = Depends(verify_token)):
    """Delete secret from vault"""
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM secrets WHERE path = $1", path)
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Secret not found")
        
        # Log deletion
        await conn.execute(
            "INSERT INTO audit_log (operation, path, token_hash) VALUES ($1, $2, $3)",
            "delete", path, hash_token(token)
        )
        
        return {"success": True}

@app.get("/v1/sys/audit")
async def get_audit_logs(
    limit: int = 100,
    token: str = Depends(verify_token)
):
    """Get audit logs"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT $1",
            limit
        )
        
        return {
            "audit_logs": [
                {
                    "timestamp": row['timestamp'].isoformat(),
                    "operation": row['operation'],
                    "path": row['path'],
                    "token_hash": row['token_hash']
                }
                for row in rows
            ]
        }

@app.post("/v1/secret/rotate/{path:path}")
async def rotate_secret(path: str, token: str = Depends(verify_token)):
    """Manually trigger secret rotation"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT data FROM secrets WHERE path = $1", path)
        
        if not row:
            raise HTTPException(status_code=404, detail="Secret not found")
        
        # Generate new secret value
        data = row['data']
        if isinstance(data, str):
            import json
            data = json.loads(data)
        for key in data.keys():
            if 'password' in key.lower() or 'token' in key.lower() or 'key' in key.lower() or 'api' in key.lower():
                data[key] = secrets.token_urlsafe(32)
        
        await conn.execute(
            "UPDATE secrets SET data = $1, last_rotated = CURRENT_TIMESTAMP, version = version + 1 WHERE path = $2",
            json.dumps(data), path
        )
        
        # Log rotation
        await conn.execute(
            "INSERT INTO audit_log (operation, path, token_hash) VALUES ($1, $2, $3)",
            "rotate", path, hash_token(token)
        )
        
        return {"success": True, "rotated_at": datetime.utcnow().isoformat()}

async def rotation_worker():
    """Background worker for automatic secret rotation"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            async with db_pool.acquire() as conn:
                # Find secrets that need rotation
                rows = await conn.fetch('''
                    SELECT path, data, last_rotated 
                    FROM secrets 
                    WHERE rotation_enabled = TRUE 
                    AND last_rotated < CURRENT_TIMESTAMP - INTERVAL '5 minutes'
                ''')
                
                for row in rows:
                    path = row['path']
                    data = row['data']
                    
                    # Rotate secrets
                    for key in data.keys():
                        if 'password' in key.lower() or 'token' in key.lower() or 'key' in key.lower():
                            data[key] = secrets.token_urlsafe(32)
                    
                    await conn.execute(
                        "UPDATE secrets SET data = $1, last_rotated = CURRENT_TIMESTAMP, version = version + 1 WHERE path = $2",
                        json.dumps(data), path
                    )
                    
                    print(f"Auto-rotated secret: {path}")
                    
        except Exception as e:
            print(f"Rotation worker error: {e}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vault-simulator"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    async with db_pool.acquire() as conn:
        secret_count = await conn.fetchval("SELECT COUNT(*) FROM secrets")
        audit_count = await conn.fetchval("SELECT COUNT(*) FROM audit_log")
    
    return {
        "vault_secrets_total": secret_count,
        "vault_audit_logs_total": audit_count,
        "vault_tokens_active": len(VALID_TOKENS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
