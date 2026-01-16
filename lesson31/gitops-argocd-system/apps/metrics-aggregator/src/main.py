"""
ArgoCD Metrics Aggregator
Polls ArgoCD API and exposes metrics for Prometheus
"""
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
argocd_app_sync_total = Counter(
    'argocd_app_sync_total',
    'Total number of application syncs',
    ['app_name', 'status']
)

argocd_app_health_status = Gauge(
    'argocd_app_health_status',
    'Application health status (1=Healthy, 0=Degraded, -1=Missing)',
    ['app_name', 'namespace']
)

argocd_app_sync_duration = Histogram(
    'argocd_app_sync_duration_seconds',
    'Application sync duration',
    ['app_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

argocd_app_out_of_sync = Gauge(
    'argocd_app_out_of_sync',
    'Number of applications out of sync',
    ['app_name']
)


class ApplicationStatus(BaseModel):
    """ArgoCD Application Status Model"""
    name: str
    namespace: str
    sync_status: str
    health_status: str
    last_sync: Optional[datetime] = None
    sync_duration: Optional[float] = None
    repo_url: str = ""
    target_revision: str = ""


class MetricsAggregator:
    """Aggregates metrics from ArgoCD API"""
    
    def __init__(self, argocd_server: str, argocd_token: str):
        self.argocd_server = argocd_server
        self.headers = {
            "Authorization": f"Bearer {argocd_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)
    
    async def get_applications(self) -> List[Dict]:
        """Fetch all applications from ArgoCD"""
        try:
            url = f"{self.argocd_server}/api/v1/applications"
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('items', [])
        except Exception as e:
            logger.error(f"Failed to fetch applications: {e}")
            return []
    
    async def update_metrics(self):
        """Update Prometheus metrics from ArgoCD state"""
        applications = await self.get_applications()
        
        for app in applications:
            try:
                metadata = app.get('metadata', {})
                status = app.get('status', {})
                
                app_name = metadata.get('name', 'unknown')
                namespace = metadata.get('namespace', 'default')
                
                sync_status = status.get('sync', {}).get('status', 'Unknown')
                health_status = status.get('health', {}).get('status', 'Unknown')
                
                # Update sync status counter
                argocd_app_sync_total.labels(
                    app_name=app_name,
                    status=sync_status
                ).inc()
                
                # Update health status gauge
                health_value = 1 if health_status == 'Healthy' else 0 if health_status == 'Degraded' else -1
                argocd_app_health_status.labels(
                    app_name=app_name,
                    namespace=namespace
                ).set(health_value)
                
                # Update out of sync status
                out_of_sync_value = 1 if sync_status != 'Synced' else 0
                argocd_app_out_of_sync.labels(app_name=app_name).set(out_of_sync_value)
                
                # Update sync duration if available
                operation_state = status.get('operationState', {})
                if operation_state and 'finishedAt' in operation_state and 'startedAt' in operation_state:
                    started = datetime.fromisoformat(operation_state['startedAt'].replace('Z', '+00:00'))
                    finished = datetime.fromisoformat(operation_state['finishedAt'].replace('Z', '+00:00'))
                    duration = (finished - started).total_seconds()
                    argocd_app_sync_duration.labels(app_name=app_name).observe(duration)
                
            except Exception as e:
                logger.error(f"Error processing application {app.get('metadata', {}).get('name', 'unknown')}: {e}")
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()


# Global aggregator instance
aggregator: Optional[MetricsAggregator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global aggregator
    
    # Startup
    argocd_server = os.getenv('ARGOCD_SERVER', 'https://argocd-server.argocd.svc.cluster.local')
    argocd_token = os.getenv('ARGOCD_TOKEN', '').strip()  # Remove any whitespace/newlines
    
    aggregator = MetricsAggregator(argocd_server, argocd_token)
    
    # Start background metrics collection
    asyncio.create_task(metrics_collection_loop())
    
    yield
    
    # Shutdown
    if aggregator:
        await aggregator.close()


app = FastAPI(title="ArgoCD Metrics Aggregator", lifespan=lifespan)


async def metrics_collection_loop():
    """Background task to collect metrics periodically"""
    while True:
        try:
            if aggregator:
                await aggregator.update_metrics()
            await asyncio.sleep(30)  # Poll every 30 seconds
        except Exception as e:
            logger.error(f"Error in metrics collection loop: {e}")
            await asyncio.sleep(30)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


@app.get("/api/applications")
async def get_applications():
    """Get current application status"""
    if not aggregator:
        raise HTTPException(status_code=503, detail="Aggregator not initialized")
    
    applications = await aggregator.get_applications()
    
    result = []
    for app in applications:
        metadata = app.get('metadata', {})
        status = app.get('status', {})
        spec = app.get('spec', {})
        
        result.append({
            'name': metadata.get('name'),
            'namespace': metadata.get('namespace'),
            'sync_status': status.get('sync', {}).get('status'),
            'health_status': status.get('health', {}).get('status'),
            'repo_url': spec.get('source', {}).get('repoURL'),
            'target_revision': spec.get('source', {}).get('targetRevision', 'HEAD')
        })
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
