"""
Analytics Service - Aggregate and analyze log data
Provides real-time analytics and insights
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from prometheus_client import generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Service")

# In-memory analytics storage
analytics_data = defaultdict(lambda: defaultdict(int))

class HealthResponse(BaseModel):
    status: str
    timestamp: str

class AnalyticsSummary(BaseModel):
    time_range: str
    total_logs: int
    error_rate: float
    top_services: List[Dict[str, Any]]
    alerts: List[str]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/summary", response_model=AnalyticsSummary)
async def get_summary(time_range: str = "1h"):
    """Get analytics summary"""
    # Simulate analytics data
    total_logs = 15420
    errors = 234
    error_rate = (errors / total_logs) * 100
    
    top_services = [
        {"service": "api-gateway", "count": 5200},
        {"service": "auth-service", "count": 3100},
        {"service": "log-processor", "count": 4800}
    ]
    
    alerts = []
    if error_rate > 5.0:
        alerts.append("High error rate detected")
    
    return AnalyticsSummary(
        time_range=time_range,
        total_logs=total_logs,
        error_rate=round(error_rate, 2),
        top_services=top_services,
        alerts=alerts
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
