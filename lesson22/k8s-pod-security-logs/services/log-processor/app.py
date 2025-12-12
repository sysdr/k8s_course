"""
Log Processor Service - Restricted Pod Security Policy
Processes and enriches log entries with strict security constraints
Demonstrates read-only root filesystem and capability dropping
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict
import asyncio
import logging
import os
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Log Processor Service",
    description="Log processing with restricted security policy",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use /tmp for any writes (mounted as emptyDir in restricted mode)
TMP_DIR = "/tmp/app-data"

@app.on_event("startup")
async def startup_event():
    """Initialize processor on startup"""
    # Ensure tmp directory exists (writable in restricted mode)
    os.makedirs(TMP_DIR, exist_ok=True)
    logger.info("Log processor started with restricted security context")
    logger.info(f"Running as UID: {os.getuid()}, GID: {os.getgid()}")
    logger.info(f"Writable temp directory: {TMP_DIR}")

class ProcessedLog(BaseModel):
    """Processed log entry with enrichment"""
    original_timestamp: datetime
    processed_timestamp: datetime = datetime.utcnow()
    level: str
    service: str
    tenant: str
    message: str
    enrichment: Optional[Dict] = {}
    security_context: Dict = {}

async def enrich_log(log_data: dict) -> ProcessedLog:
    """
    Enrich log entry with additional context
    
    This demonstrates processing logic in a restricted security context:
    - No root privileges
    - No dangerous capabilities
    - Read-only root filesystem
    - All writes go to /tmp (emptyDir)
    """
    try:
        # Add enrichment data
        enrichment = {
            "processor_version": "1.0.0",
            "processing_time_ms": 5,
            "security_policy": "restricted",
            "hostname": os.getenv("HOSTNAME", "unknown")
        }
        
        # Add security context information
        security_context = {
            "uid": os.getuid(),
            "gid": os.getgid(),
            "capabilities": "none (all dropped)",
            "root_filesystem": "read-only",
            "privilege_escalation": "disabled"
        }
        
        processed = ProcessedLog(
            original_timestamp=log_data.get("timestamp", datetime.utcnow()),
            level=log_data.get("level", "INFO"),
            service=log_data.get("service", "unknown"),
            tenant=log_data.get("tenant", "unknown"),
            message=log_data.get("message", ""),
            enrichment=enrichment,
            security_context=security_context
        )
        
        # Write to tmp directory (only writable location in restricted mode)
        tmp_file = os.path.join(TMP_DIR, f"processed_{datetime.utcnow().timestamp()}.json")
        with open(tmp_file, 'w') as f:
            json.dump(processed.dict(), f, default=str)
        
        logger.info(f"Processed log for tenant: {processed.tenant}")
        return processed
        
    except Exception as e:
        logger.error(f"Error enriching log: {e}")
        raise

@app.post("/process")
async def process_log(log_data: dict):
    """Process a single log entry"""
    try:
        processed = await enrich_log(log_data)
        return {
            "status": "processed",
            "data": processed.dict()
        }
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    """Health check for Kubernetes probes"""
    # Verify we can write to tmp directory
    try:
        test_file = os.path.join(TMP_DIR, ".health_check")
        with open(test_file, 'w') as f:
            f.write(str(datetime.utcnow()))
        os.remove(test_file)
        tmp_writable = True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        tmp_writable = False
    
    return {
        "status": "healthy" if tmp_writable else "degraded",
        "service": "log-processor",
        "security_policy": "restricted",
        "uid": os.getuid(),
        "gid": os.getgid(),
        "tmp_writable": tmp_writable,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/security-info")
async def security_info():
    """Return security context information"""
    return {
        "policy": "restricted",
        "user_id": os.getuid(),
        "group_id": os.getgid(),
        "capabilities": "ALL capabilities dropped",
        "root_filesystem": "read-only",
        "privilege_escalation": "disabled",
        "seccomp_profile": "RuntimeDefault",
        "writable_paths": ["/tmp"],
        "compliance": {
            "runAsNonRoot": True,
            "readOnlyRootFilesystem": True,
            "allowPrivilegeEscalation": False,
            "capabilities_dropped": ["ALL"]
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "log-processor",
        "version": "1.0.0",
        "security_policy": "restricted",
        "description": "Demonstrates Kubernetes Restricted pod security standard"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
