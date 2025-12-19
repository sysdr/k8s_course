"""
Secrets Rotation Service - Orchestrates automatic secret rotation
Coordinates with Vault and Kubernetes to rotate secrets safely
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import httpx
import json
from datetime import datetime, timedelta
import os

app = FastAPI(title="Secrets Rotation Service", version="1.0.0")

# Vault configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault-simulator:8080")
VAULT_TOKEN = None

class RotationPolicy(BaseModel):
    secret_path: str
    rotation_interval: int = 300  # seconds
    grace_period: int = 90
    last_rotated: Optional[datetime] = None

# Rotation policies
rotation_policies: Dict[str, RotationPolicy] = {}

async def get_vault_token():
    """Get Vault token"""
    global VAULT_TOKEN
    
    if not VAULT_TOKEN:
        # Get token from environment variable or create new token
        VAULT_TOKEN = os.getenv("VAULT_TOKEN")
        
        if not VAULT_TOKEN:
            async with httpx.AsyncClient() as client:
                # Create new token
                response = await client.post(f"{VAULT_ADDR}/v1/auth/token/create")
                data = response.json()
                VAULT_TOKEN = data['auth']['client_token']
    
    return VAULT_TOKEN

@app.on_event("startup")
async def startup():
    """Initialize rotation service"""
    # Register secrets for rotation
    rotation_policies.update({
        "ingestion-api-keys": RotationPolicy(
            secret_path="secret/data/ingestion-api-keys",
            rotation_interval=300
        ),
        "database-credentials": RotationPolicy(
            secret_path="secret/data/database-credentials",
            rotation_interval=600
        ),
        "external-api-keys": RotationPolicy(
            secret_path="secret/data/external-api-keys",
            rotation_interval=450
        )
    })
    
    # Start rotation worker
    asyncio.create_task(rotation_worker())
    
    print("Secrets Rotation Service started")

async def rotate_secret(policy: RotationPolicy):
    """Rotate a secret"""
    try:
        token = await get_vault_token()
        
        async with httpx.AsyncClient() as client:
            # Trigger rotation in Vault
            response = await client.post(
                f"{VAULT_ADDR}/v1/secret/rotate/{policy.secret_path.replace('secret/data/', '')}",
                headers={"X-Vault-Token": token}
            )
            
            if response.status_code == 200:
                policy.last_rotated = datetime.utcnow()
                print(f"Rotated secret: {policy.secret_path}")
                return True
            else:
                print(f"Failed to rotate {policy.secret_path}: {response.text}")
                return False
                
    except Exception as e:
        print(f"Error rotating secret {policy.secret_path}: {e}")
        return False

async def rotation_worker():
    """Background worker for automatic rotation"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            now = datetime.utcnow()
            
            for name, policy in rotation_policies.items():
                # Check if rotation needed
                if policy.last_rotated is None:
                    # First rotation
                    await rotate_secret(policy)
                else:
                    time_since_rotation = (now - policy.last_rotated).total_seconds()
                    
                    if time_since_rotation >= policy.rotation_interval:
                        await rotate_secret(policy)
                        
        except Exception as e:
            print(f"Rotation worker error: {e}")

@app.get("/api/v1/rotation/status")
async def get_rotation_status():
    """Get rotation status for all secrets"""
    return {
        "policies": [
            {
                "name": name,
                "secret_path": policy.secret_path,
                "rotation_interval": policy.rotation_interval,
                "last_rotated": policy.last_rotated.isoformat() if policy.last_rotated else None,
                "next_rotation": (policy.last_rotated + timedelta(seconds=policy.rotation_interval)).isoformat() 
                    if policy.last_rotated else "pending"
            }
            for name, policy in rotation_policies.items()
        ]
    }

@app.post("/api/v1/rotation/trigger/{secret_name}")
async def trigger_rotation(secret_name: str):
    """Manually trigger secret rotation"""
    if secret_name not in rotation_policies:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    policy = rotation_policies[secret_name]
    success = await rotate_secret(policy)
    
    if success:
        return {"status": "success", "rotated_at": policy.last_rotated.isoformat()}
    else:
        raise HTTPException(status_code=500, detail="Rotation failed")

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "secrets-rotation",
        "managed_secrets": len(rotation_policies)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
