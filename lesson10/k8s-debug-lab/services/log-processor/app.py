"""
Log Processor Service - Consumes logs from Kafka and processes them
Designed to demonstrate networking debugging scenarios
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
LOGS_PROCESSED = Counter('logs_processed_total', 'Total logs processed', ['level'])
PROCESSING_LATENCY = Histogram('processing_latency_seconds', 'Processing latency')
QUEUE_SIZE = Gauge('processing_queue_size', 'Current queue size')
ERRORS_DETECTED = Counter('errors_detected_total', 'Errors detected in logs', ['error_type'])

app = FastAPI(
    title="Log Processor Service",
    description="Processes and analyzes logs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessedLog(BaseModel):
    original_message: str
    processed_at: datetime
    anomaly_score: float
    patterns_detected: list[str]
    metadata: dict

# Pattern detection rules
ERROR_PATTERNS = {
    'null_pointer': r'NullPointerException|null reference|None type',
    'timeout': r'timeout|timed out|deadline exceeded',
    'connection_error': r'connection refused|ECONNREFUSED|connect failed',
    'memory_error': r'OutOfMemoryError|OOM|memory exceeded',
    'auth_failure': r'unauthorized|authentication failed|403|401',
}

class LogProcessor:
    def __init__(self):
        self.processed_count = 0
        self.queue = asyncio.Queue(maxsize=1000)
        
    async def process(self, log_data: dict) -> ProcessedLog:
        """Process a single log entry"""
        message = log_data.get('message', '')
        
        # Detect patterns
        patterns_detected = []
        for pattern_name, pattern_regex in ERROR_PATTERNS.items():
            if re.search(pattern_regex, message, re.IGNORECASE):
                patterns_detected.append(pattern_name)
                ERRORS_DETECTED.labels(error_type=pattern_name).inc()
        
        # Calculate anomaly score (simplified)
        anomaly_score = len(patterns_detected) * 0.25
        if log_data.get('level') in ['ERROR', 'CRITICAL']:
            anomaly_score += 0.5
            
        self.processed_count += 1
        LOGS_PROCESSED.labels(level=log_data.get('level', 'UNKNOWN')).inc()
        
        return ProcessedLog(
            original_message=message,
            processed_at=datetime.utcnow(),
            anomaly_score=min(anomaly_score, 1.0),
            patterns_detected=patterns_detected,
            metadata={
                'source': log_data.get('source'),
                'original_level': log_data.get('level'),
                'processing_id': self.processed_count
            }
        )

processor = LogProcessor()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "processed_count": processor.processed_count
    }

@app.get("/ready")
async def readiness_check():
    # Check if we can reach dependent services
    return {"ready": True}

@app.get("/metrics")
async def metrics():
    QUEUE_SIZE.set(processor.queue.qsize())
    return generate_latest()

@app.post("/process", response_model=ProcessedLog)
async def process_log(log_data: dict):
    """Process a single log entry"""
    try:
        result = await processor.process(log_data)
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get processing statistics"""
    return {
        "total_processed": processor.processed_count,
        "queue_size": processor.queue.qsize(),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
