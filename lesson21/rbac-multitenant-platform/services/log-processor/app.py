"""
Log Processor Service - Reads logs from pods and processes them
Requires RBAC: get, list, watch on pods and pods/log
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Processor Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Kubernetes client
try:
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes config")
except:
    config.load_kube_config()
    logger.info("Loaded local Kubernetes config")

v1 = client.CoreV1Api()
NAMESPACE = os.getenv("POD_NAMESPACE", "analytics")

class LogEntry(BaseModel):
    timestamp: str
    pod_name: str
    namespace: str
    message: str
    level: str

class RBACCheck(BaseModel):
    resource: str
    verb: str
    allowed: bool
    serviceaccount: str

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "log-processor"}

@app.get("/api/logs/{namespace}/{pod_name}")
async def get_pod_logs(namespace: str, pod_name: str, tail_lines: int = 100) -> dict:
    """Fetch logs from a specific pod"""
    try:
        # Check RBAC permissions first
        auth_api = client.AuthorizationV1Api()
        sar = client.V1SelfSubjectAccessReview(
            spec=client.V1SelfSubjectAccessReviewSpec(
                resource_attributes=client.V1ResourceAttributes(
                    namespace=namespace,
                    verb="get",
                    resource="pods/log"
                )
            )
        )
        response = auth_api.create_self_subject_access_review(sar)
        
        if not response.status.allowed:
            raise HTTPException(
                status_code=403, 
                detail=f"ServiceAccount not authorized to read logs in namespace {namespace}"
            )
        
        # Fetch logs
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines
        )
        
        # Parse and structure logs
        log_entries = []
        for line in logs.split('\n'):
            if line.strip():
                log_entries.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "message": line,
                    "level": "INFO"
                })
        
        return {
            "pod": pod_name,
            "namespace": namespace,
            "log_count": len(log_entries),
            "logs": log_entries[:tail_lines]
        }
        
    except client.exceptions.ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise HTTPException(status_code=e.status, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pods/{namespace}")
async def list_pods(namespace: str) -> dict:
    """List all pods in a namespace"""
    try:
        # Check RBAC permissions
        auth_api = client.AuthorizationV1Api()
        sar = client.V1SelfSubjectAccessReview(
            spec=client.V1SelfSubjectAccessReviewSpec(
                resource_attributes=client.V1ResourceAttributes(
                    namespace=namespace,
                    verb="list",
                    resource="pods"
                )
            )
        )
        response = auth_api.create_self_subject_access_review(sar)
        
        if not response.status.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"ServiceAccount not authorized to list pods in namespace {namespace}"
            )
        
        pods = v1.list_namespaced_pod(namespace)
        
        pod_list = []
        for pod in pods.items:
            pod_list.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "created": pod.metadata.creation_timestamp.isoformat(),
                "serviceaccount": pod.spec.service_account_name
            })
        
        return {
            "namespace": namespace,
            "pod_count": len(pod_list),
            "pods": pod_list
        }
        
    except client.exceptions.ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise HTTPException(status_code=e.status, detail=str(e))

@app.get("/api/rbac/check")
async def check_rbac_permissions() -> dict:
    """Check what this ServiceAccount can do"""
    try:
        auth_api = client.AuthorizationV1Api()
        
        checks = [
            {"resource": "pods", "verb": "get"},
            {"resource": "pods", "verb": "list"},
            {"resource": "pods", "verb": "create"},
            {"resource": "pods", "verb": "delete"},
            {"resource": "pods/log", "verb": "get"},
            {"resource": "secrets", "verb": "get"},
            {"resource": "configmaps", "verb": "get"},
            {"resource": "services", "verb": "list"},
        ]
        
        results = []
        for check in checks:
            sar = client.V1SelfSubjectAccessReview(
                spec=client.V1SelfSubjectAccessReviewSpec(
                    resource_attributes=client.V1ResourceAttributes(
                        namespace=NAMESPACE,
                        verb=check["verb"],
                        resource=check["resource"]
                    )
                )
            )
            response = auth_api.create_self_subject_access_review(sar)
            
            results.append({
                "resource": check["resource"],
                "verb": check["verb"],
                "allowed": response.status.allowed,
                "reason": response.status.reason or "N/A"
            })
        
        return {
            "serviceaccount": os.getenv("SERVICE_ACCOUNT", "unknown"),
            "namespace": NAMESPACE,
            "permissions": results
        }
        
    except Exception as e:
        logger.error(f"Error checking RBAC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
