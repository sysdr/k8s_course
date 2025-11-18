"""
Log Processor Service - Process and analyze log entries
Performs aggregation, anomaly detection, and statistics
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Processor Service", version="1.0.0")

# In-memory statistics (in production, use TimescaleDB or ClickHouse)
log_stats = {
    "total_processed": 0,
    "by_level": defaultdict(int),
    "by_service": defaultdict(int),
    "error_rate": deque(maxlen=100),
    "processing_times": deque(maxlen=1000)
}

class ProcessedLog(BaseModel):
    log_id: str
    processed_at: str
    anomaly_score: float
    tags: List[str]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "log-processor",
        "timestamp": datetime.utcnow().isoformat(),
        "processed_count": log_stats["total_processed"]
    }

@app.post("/process")
async def process_log(log_data: Dict):
    """
    Process individual log entry
    Performs enrichment, anomaly detection, and aggregation
    """
    start_time = datetime.utcnow()
    
    try:
        # Extract log details
        level = log_data.get("level", "INFO")
        service = log_data.get("service", "unknown")
        message = log_data.get("message", "")
        
        # Update statistics
        log_stats["total_processed"] += 1
        log_stats["by_level"][level] += 1
        log_stats["by_service"][service] += 1
        
        # Simple anomaly detection
        anomaly_score = 0.0
        tags = []
        
        if level == "ERROR":
            anomaly_score = 0.8
            tags.append("error")
            log_stats["error_rate"].append(1)
        else:
            log_stats["error_rate"].append(0)
        
        if "exception" in message.lower() or "failed" in message.lower():
            anomaly_score = max(anomaly_score, 0.6)
            tags.append("exception")
        
        # Track processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        log_stats["processing_times"].append(processing_time)
        
        return ProcessedLog(
            log_id=f"proc-{log_stats['total_processed']}",
            processed_at=datetime.utcnow().isoformat(),
            anomaly_score=anomaly_score,
            tags=tags
        )
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise

@app.get("/stats")
async def get_stats():
    """
    Get processing statistics
    Used by API Gateway for dashboard
    """
    # Calculate error rate
    recent_errors = sum(log_stats["error_rate"]) if log_stats["error_rate"] else 0
    total_recent = len(log_stats["error_rate"]) if log_stats["error_rate"] else 1
    error_rate = (recent_errors / total_recent) * 100
    
    # Calculate average processing time
    avg_processing_time = (
        sum(log_stats["processing_times"]) / len(log_stats["processing_times"])
        if log_stats["processing_times"] else 0
    )
    
    return {
        "total_processed": log_stats["total_processed"],
        "by_level": dict(log_stats["by_level"]),
        "by_service": dict(log_stats["by_service"]),
        "error_rate_percentage": round(error_rate, 2),
        "avg_processing_time_ms": round(avg_processing_time * 1000, 2),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    error_rate = sum(log_stats["error_rate"]) / max(len(log_stats["error_rate"]), 1)
    avg_processing_time = sum(log_stats["processing_times"]) / max(len(log_stats["processing_times"]), 1)
    metrics_text = f"""# HELP log_processor_processed_total Total logs processed
# TYPE log_processor_processed_total counter
log_processor_processed_total{{service="log-processor"}} {log_stats["total_processed"]}
# HELP log_processor_error_rate Error rate
# TYPE log_processor_error_rate gauge
log_processor_error_rate{{service="log-processor"}} {error_rate}
# HELP log_processor_processing_time_avg Average processing time in seconds
# TYPE log_processor_processing_time_avg gauge
log_processor_processing_time_avg{{service="log-processor"}} {avg_processing_time}
"""
    return Response(content=metrics_text, media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
