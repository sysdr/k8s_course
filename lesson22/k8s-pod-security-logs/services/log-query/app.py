"""
Log Query Service - Baseline Pod Security Policy
Provides query interface for stored logs
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Log Query Service",
    description="Query interface for log data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/query")
async def query_logs(
    tenant: Optional[str] = None,
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000)
):
    """Query logs with filters"""
    # Mock data for demonstration
    mock_logs = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "service": "api-gateway",
            "tenant": "public",
            "message": "Request processed",
            "security_policy": "baseline"
        }
    ]
    
    return {
        "total": len(mock_logs),
        "logs": mock_logs,
        "filters": {
            "tenant": tenant,
            "service": service,
            "level": level,
            "limit": limit
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "log-query",
        "security_policy": "baseline"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
