from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Dict, List
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
analytics_requests = Counter('analytics_requests_total', 'Total analytics requests', ['type'])
analytics_latency = Histogram('analytics_latency_seconds', 'Analytics computation latency')

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "analytics-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def ready():
    return {"status": "ready"}

@app.get("/api/analytics/summary")
async def get_summary():
    try:
        with analytics_latency.time():
            analytics_requests.labels(type="summary").inc()
            
            # Simulate analytics computation
            summary = {
            "total_logs": random.randint(10000, 50000),
            "logs_by_level": {
                "DEBUG": random.randint(1000, 5000),
                "INFO": random.randint(5000, 20000),
                "WARNING": random.randint(1000, 5000),
                "ERROR": random.randint(500, 2000),
                "CRITICAL": random.randint(10, 100)
            },
            "top_sources": [
                {"source": "web-server", "count": random.randint(5000, 15000)},
                {"source": "api-gateway", "count": random.randint(3000, 10000)},
                {"source": "database", "count": random.randint(1000, 5000)},
                {"source": "cache", "count": random.randint(500, 2000)},
                {"source": "worker", "count": random.randint(200, 1000)}
            ],
                "error_rate": round(random.uniform(0.5, 3.5), 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Generated analytics summary")
            return summary
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@app.get("/api/analytics/timeseries")
async def get_timeseries(hours: int = 24):
    analytics_requests.labels(type="timeseries").inc()
    
    # Generate time series data
    now = datetime.utcnow()
    data_points = []
    
    for i in range(hours):
        timestamp = now - timedelta(hours=hours-i)
        data_points.append({
            "timestamp": timestamp.isoformat(),
            "total": random.randint(100, 1000),
            "errors": random.randint(5, 50),
            "warnings": random.randint(20, 150)
        })
    
    return {
        "timeframe": f"{hours}h",
        "data_points": data_points,
        "generated_at": now.isoformat()
    }

@app.get("/api/analytics/trends")
async def get_trends():
    analytics_requests.labels(type="trends").inc()
    
    trends = {
        "error_trend": random.choice(["increasing", "decreasing", "stable"]),
        "volume_trend": random.choice(["increasing", "decreasing", "stable"]),
        "top_error_messages": [
            {"message": "Connection timeout", "count": random.randint(50, 500)},
            {"message": "Authentication failed", "count": random.randint(30, 300)},
            {"message": "Resource not found", "count": random.randint(20, 200)}
        ],
        "peak_hours": [9, 10, 14, 15, 16],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return trends

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
