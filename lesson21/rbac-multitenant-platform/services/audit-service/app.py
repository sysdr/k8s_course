"""
Audit Service - Tracks and logs RBAC permission checks
Requires RBAC: get on events, limited read access
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from pydantic import BaseModel
from typing import List
import os
import logging
from datetime import datetime, timedelta
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audit Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()

class AuditEvent(BaseModel):
    timestamp: str
    namespace: str
    serviceaccount: str
    resource: str
    verb: str
    allowed: bool

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "audit-service"}

@app.get("/api/audit/events/{namespace}")
async def get_audit_events(namespace: str, hours: int = 24) -> dict:
    """Get audit events for a namespace"""
    try:
        # Check permissions to view events
        auth_api = client.AuthorizationV1Api()
        sar = client.V1SelfSubjectAccessReview(
            spec=client.V1SelfSubjectAccessReviewSpec(
                resource_attributes=client.V1ResourceAttributes(
                    namespace=namespace,
                    verb="list",
                    resource="events"
                )
            )
        )
        response = auth_api.create_self_subject_access_review(sar)
        
        if not response.status.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"ServiceAccount not authorized to list events in namespace {namespace}"
            )
        
        events = v1.list_namespaced_event(namespace)
        
        # Filter RBAC-related events
        rbac_events = []
        for event in events.items:
            if event.reason in ["FailedCreate", "FailedUpdate", "FailedDelete", "Forbidden"]:
                rbac_events.append({
                    "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else event.event_time.isoformat(),
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "object": f"{event.involved_object.kind}/{event.involved_object.name}"
                })
        
        return {
            "namespace": namespace,
            "hours": hours,
            "event_count": len(rbac_events),
            "events": rbac_events[-100:]  # Last 100 events
        }
        
    except client.exceptions.ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise HTTPException(status_code=e.status, detail=str(e))

@app.get("/api/audit/permission-denials")
async def get_permission_denials() -> dict:
    """Get summary of permission denials across cluster"""
    try:
        # This would require cluster-wide event access
        # For demo, we'll check accessible namespaces
        auth_api = client.AuthorizationV1Api()
        
        # Check if we can list events cluster-wide
        sar = client.V1SelfSubjectAccessReview(
            spec=client.V1SelfSubjectAccessReviewSpec(
                resource_attributes=client.V1ResourceAttributes(
                    verb="list",
                    resource="events"
                )
            )
        )
        response = auth_api.create_self_subject_access_review(sar)
        
        if not response.status.allowed:
            return {
                "error": "ServiceAccount lacks cluster-wide event access",
                "requires": "ClusterRole with get, list on events",
                "current_permissions": "namespace-scoped only"
            }
        
        all_events = v1.list_event_for_all_namespaces()
        
        denial_summary = Counter()
        for event in all_events.items:
            if event.reason == "Forbidden":
                denial_summary[event.involved_object.namespace] += 1
        
        return {
            "total_denials": sum(denial_summary.values()),
            "by_namespace": dict(denial_summary),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting denials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
