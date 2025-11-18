"""
Query Service - Search and retrieve logs
Provides filtering, aggregation, and export capabilities
"""
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Query Service", version="1.0.0")

# Mock log storage (in production, use PostgreSQL/TimescaleDB)
mock_logs = []

class QueryRequest(BaseModel):
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100

class LogResult(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "query-service",
        "timestamp": datetime.utcnow().isoformat(),
        "indexed_logs": len(mock_logs)
    }

@app.post("/query")
async def query_logs(query: QueryRequest) -> Dict[str, Any]:
    """
    Query logs with filtering
    Supports service, level, and time range filters
    """
    # Generate mock results for demonstration
    results = []
    services = ["api-gateway", "log-processor", "log-ingestion", "query-service"]
    levels = ["INFO", "WARN", "ERROR"]
    
    target_service = query.service if query.service else random.choice(services)
    target_level = query.level if query.level else random.choice(levels)
    
    # Generate sample logs
    for i in range(min(query.limit, 20)):
        timestamp = datetime.utcnow() - timedelta(minutes=random.randint(0, 60))
        results.append(LogResult(
            timestamp=timestamp.isoformat(),
            level=target_level,
            service=target_service,
            message=f"Sample log message {i} from {target_service}",
            metadata={"query_id": f"q-{i}", "index": i}
        ))
    
    return {
        "query": query.dict(),
        "total_results": len(results),
        "results": [r.dict() for r in results],
        "query_time_ms": random.uniform(10, 50)
    }

@app.get("/services")
async def list_services():
    """List all services with log entries"""
    return {
        "services": ["api-gateway", "log-processor", "log-ingestion", "query-service"],
        "count": 4
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    from fastapi.responses import Response
    metrics_text = f"""# HELP query_service_requests_total Total query requests
# TYPE query_service_requests_total counter
query_service_requests_total{{service="query-service"}} 1000
# HELP query_service_indexed_logs Number of indexed logs
# TYPE query_service_indexed_logs gauge
query_service_indexed_logs{{service="query-service"}} {len(mock_logs)}
# HELP query_service_avg_query_time_seconds Average query time in seconds
# TYPE query_service_avg_query_time_seconds gauge
query_service_avg_query_time_seconds{{service="query-service"}} 0.025
"""
    return Response(content=metrics_text, media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
