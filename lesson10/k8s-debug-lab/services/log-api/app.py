"""
Log API Service - Provides query interface for processed logs
Used to demonstrate service discovery and DNS issues
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
QUERIES_TOTAL = Counter('api_queries_total', 'Total API queries', ['endpoint'])
QUERY_LATENCY = Histogram('api_query_latency_seconds', 'Query latency')

app = FastAPI(
    title="Log API Service",
    description="Query interface for log analytics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogSummary(BaseModel):
    total_logs: int
    by_level: dict
    by_source: dict
    time_range: dict
    anomaly_count: int

class LogQuery(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    level: Optional[str] = None
    source: Optional[str] = None
    pattern: Optional[str] = None
    limit: int = 100

# Simulated log storage
class LogStore:
    def __init__(self):
        self.logs = []
        self.next_id = 0
        self._generate_sample_data()
        
    def _generate_sample_data(self):
        """Generate sample log data for queries"""
        sources = ['web-server', 'api-gateway', 'auth-service', 'database', 'cache-service']
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for i in range(100):
            self.logs.append({
                'id': self.next_id,
                'timestamp': (datetime.utcnow() - timedelta(hours=i % 24)).isoformat(),
                'level': levels[i % len(levels)],
                'source': sources[i % len(sources)],
                'message': f'Sample log message {i}',
                'anomaly_score': (i % 10) / 10
            })
            self.next_id += 1
    
    def add_log(self, level: str, source: str, message: str, anomaly_score: float = 0.0):
        """Add a new log entry"""
        log_entry = {
            'id': self.next_id,
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'source': source,
            'message': message,
            'anomaly_score': anomaly_score
        }
        self.logs.append(log_entry)
        self.next_id += 1
        # Keep only last 1000 logs to prevent memory issues
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
    
    def query(self, query: LogQuery) -> List[dict]:
        """Query logs with filters"""
        results = self.logs.copy()
        
        if query.level:
            results = [l for l in results if l['level'] == query.level]
        if query.source:
            results = [l for l in results if l['source'] == query.source]
            
        return results[:query.limit]
    
    def get_summary(self) -> LogSummary:
        """Get summary statistics"""
        by_level = {}
        by_source = {}
        anomaly_count = 0
        
        for log in self.logs:
            level = log['level']
            source = log['source']
            by_level[level] = by_level.get(level, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
            if log['anomaly_score'] > 0.5:
                anomaly_count += 1
        
        return LogSummary(
            total_logs=len(self.logs),
            by_level=by_level,
            by_source=by_source,
            time_range={
                'start': self.logs[-1]['timestamp'] if self.logs else None,
                'end': self.logs[0]['timestamp'] if self.logs else None
            },
            anomaly_count=anomaly_count
        )

log_store = LogStore()

# Background task to simulate real-time log updates
async def simulate_log_updates():
    """Periodically add simulated logs to make data appear dynamic"""
    import random
    sources = ['web-server', 'api-gateway', 'auth-service', 'database', 'cache-service']
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    messages = [
        "User login successful",
        "Database connection established",
        "Cache miss for key: user:123",
        "Request timeout after 30s",
        "Memory usage at 85%",
        "Authentication failed for user",
        "Query executed in 45ms",
        "Failed to connect to external API",
        "Session expired",
        "Data validation error"
    ]
    
    while True:
        await asyncio.sleep(3)  # Add a log every 3 seconds
        level = random.choice(levels)
        source = random.choice(sources)
        message = random.choice(messages)
        anomaly_score = random.random() * 0.8  # Random anomaly score
        log_store.add_log(level, source, message, anomaly_score)
        logger.debug(f"Added simulated log: {level} from {source}")

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(simulate_log_updates())
    logger.info("Started log simulation background task")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "log_count": len(log_store.logs)
    }

@app.get("/ready")
async def readiness_check():
    return {"ready": True}

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.get("/api/v1/logs")
async def get_logs(
    level: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Query logs with optional filters"""
    QUERIES_TOTAL.labels(endpoint='logs').inc()
    
    query = LogQuery(level=level, source=source, limit=limit)
    results = log_store.query(query)
    
    return {
        "count": len(results),
        "logs": results
    }

@app.get("/api/v1/summary", response_model=LogSummary)
async def get_summary():
    """Get log summary statistics"""
    QUERIES_TOTAL.labels(endpoint='summary').inc()
    return log_store.get_summary()

@app.get("/api/v1/sources")
async def get_sources():
    """Get list of log sources"""
    QUERIES_TOTAL.labels(endpoint='sources').inc()
    sources = list(set(log['source'] for log in log_store.logs))
    return {"sources": sources}

@app.post("/api/v1/logs")
async def add_log(log_data: dict):
    """Add a new log entry (called by processor/ingester)"""
    try:
        level = log_data.get('level', 'INFO')
        source = log_data.get('source', 'unknown')
        message = log_data.get('message', '')
        anomaly_score = log_data.get('anomaly_score', 0.0)
        log_store.add_log(level, source, message, anomaly_score)
        return {"status": "added", "log_id": log_store.next_id - 1}
    except Exception as e:
        logger.error(f"Failed to add log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
