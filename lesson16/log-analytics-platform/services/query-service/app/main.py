from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Query Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
queries_executed = Counter('queries_executed_total', 'Total queries executed', ['status'])
query_latency = Histogram('query_latency_seconds', 'Query execution latency')

# Cache for demonstration (in production, use Redis)
query_cache = {}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "query-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def ready():
    return {"status": "ready"}

@app.get("/api/query")
async def query_logs(
    level: Optional[str] = Query(None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    source: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    try:
        with query_latency.time():
            # In production, query from database/Elasticsearch
            # For demo, fetch from ingestion service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://log-ingestion-service:8000/stats",
                    timeout=5.0
                )
                stats = response.json()
            
            # Simulate query results
            results = []
            for i in range(min(limit, 50)):  # Return max 50 for demo
                results.append({
                    "id": offset + i,
                    "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                    "level": level or "INFO",
                    "message": f"Sample log message {i}",
                    "source": source or "default-source",
                    "metadata": {"query_id": f"q-{i}"}
                })
            
            queries_executed.labels(status="success").inc()
            logger.info(f"Query executed: level={level}, source={source}, limit={limit}")
            
            return {
                "status": "success",
                "results": results,
                "total": len(results),
                "offset": offset,
                "limit": limit
            }
    except httpx.TimeoutException:
        queries_executed.labels(status="timeout").inc()
        raise HTTPException(status_code=504, detail="Ingestion service timeout")
    except Exception as e:
        queries_executed.labels(status="error").inc()
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/api/query/search")
async def search_logs(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=500)
):
    # Simulate full-text search
    results = [
        {
            "id": i,
            "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            "level": "INFO",
            "message": f"Log containing '{q}' - result {i}",
            "source": "search-engine",
            "score": 1.0 - (i * 0.01)
        }
        for i in range(min(limit, 20))
    ]
    
    return {
        "query": q,
        "results": results,
        "total": len(results)
    }

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
