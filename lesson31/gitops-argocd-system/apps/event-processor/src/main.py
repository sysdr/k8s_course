"""
ArgoCD Event Processor
Processes ArgoCD webhook events and stores deployment history
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeploymentEvent(BaseModel):
    """Deployment Event Model"""
    app_name: str
    namespace: str
    event_type: str  # sync-started, sync-succeeded, sync-failed
    sync_status: str
    health_status: Optional[str] = None
    revision: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: Optional[str] = None


class EventProcessor:
    """Processes and stores deployment events"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        await self.create_tables()
    
    async def create_tables(self):
        """Create required database tables"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS deployment_events (
                    id SERIAL PRIMARY KEY,
                    app_name VARCHAR(255) NOT NULL,
                    namespace VARCHAR(255) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    sync_status VARCHAR(50) NOT NULL,
                    health_status VARCHAR(50),
                    revision VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_app_name ON deployment_events(app_name);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON deployment_events(timestamp);
            ''')
    
    async def store_event(self, event: DeploymentEvent):
        """Store deployment event in database"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO deployment_events 
                (app_name, namespace, event_type, sync_status, health_status, revision, timestamp, message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''', event.app_name, event.namespace, event.event_type, event.sync_status,
                event.health_status, event.revision, event.timestamp, event.message)
    
    async def get_recent_events(self, app_name: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent deployment events"""
        async with self.pool.acquire() as conn:
            if app_name:
                rows = await conn.fetch('''
                    SELECT * FROM deployment_events 
                    WHERE app_name = $1 
                    ORDER BY timestamp DESC 
                    LIMIT $2
                ''', app_name, limit)
            else:
                rows = await conn.fetch('''
                    SELECT * FROM deployment_events 
                    ORDER BY timestamp DESC 
                    LIMIT $1
                ''', limit)
            
            return [dict(row) for row in rows]
    
    async def get_deployment_stats(self) -> Dict:
        """Get deployment statistics"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_deployments,
                    COUNT(CASE WHEN sync_status = 'Synced' THEN 1 END) as successful_deployments,
                    COUNT(CASE WHEN sync_status != 'Synced' THEN 1 END) as failed_deployments,
                    COUNT(DISTINCT app_name) as total_applications
                FROM deployment_events
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            ''')
            
            return dict(stats)
    
    async def close(self):
        """Cleanup resources"""
        if self.pool:
            await self.pool.close()


processor: Optional[EventProcessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global processor
    
    # Startup
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@postgres:5432/gitops')
    processor = EventProcessor(database_url)
    await processor.initialize()
    
    yield
    
    # Shutdown
    if processor:
        await processor.close()


app = FastAPI(title="ArgoCD Event Processor", lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/webhook/argocd")
async def argocd_webhook(event_data: Dict, background_tasks: BackgroundTasks):
    """Receive ArgoCD webhook events"""
    try:
        # Parse ArgoCD webhook payload
        app_metadata = event_data.get('metadata', {})
        app_status = event_data.get('status', {})
        
        event = DeploymentEvent(
            app_name=app_metadata.get('name', 'unknown'),
            namespace=app_metadata.get('namespace', 'default'),
            event_type=event_data.get('type', 'unknown'),
            sync_status=app_status.get('sync', {}).get('status', 'Unknown'),
            health_status=app_status.get('health', {}).get('status'),
            revision=app_status.get('sync', {}).get('revision', 'unknown'),
            message=event_data.get('message')
        )
        
        # Process event in background
        background_tasks.add_task(processor.store_event, event)
        
        return {"status": "accepted", "event_id": event.app_name}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
async def get_events(app_name: Optional[str] = None, limit: int = 100):
    """Get recent deployment events"""
    if not processor:
        raise HTTPException(status_code=503, detail="Processor not initialized")
    
    events = await processor.get_recent_events(app_name, limit)
    return {"events": events}


@app.get("/api/stats")
async def get_stats():
    """Get deployment statistics"""
    if not processor:
        raise HTTPException(status_code=503, detail="Processor not initialized")
    
    stats = await processor.get_deployment_stats()
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
