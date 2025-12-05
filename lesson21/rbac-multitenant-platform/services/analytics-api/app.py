"""
Analytics API Service - Aggregates and exposes analytics data
Requires RBAC: get, list on deployments, services, configmaps
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from pydantic import BaseModel
from typing import List, Dict
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics API Service")

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
apps_v1 = client.AppsV1Api()
rbac_v1 = client.RbacAuthorizationV1Api()

class NamespaceAnalytics(BaseModel):
    namespace: str
    pod_count: int
    service_count: int
    deployment_count: int
    serviceaccount_count: int

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics-api"}

@app.get("/api/analytics/namespaces")
async def get_namespace_analytics() -> dict:
    """Get analytics across all accessible namespaces"""
    try:
        namespaces = v1.list_namespace()
        
        analytics = []
        for ns in namespaces.items:
            namespace = ns.metadata.name
            
            # Try to list resources - will fail gracefully if we don't have permissions
            try:
                pods = v1.list_namespaced_pod(namespace)
                services = v1.list_namespaced_service(namespace)
                deployments = apps_v1.list_namespaced_deployment(namespace)
                serviceaccounts = v1.list_namespaced_service_account(namespace)
                
                analytics.append({
                    "namespace": namespace,
                    "pod_count": len(pods.items),
                    "service_count": len(services.items),
                    "deployment_count": len(deployments.items),
                    "serviceaccount_count": len(serviceaccounts.items),
                    "created": ns.metadata.creation_timestamp.isoformat()
                })
            except client.exceptions.ApiException as e:
                # Skip if we don't have permissions (403 Forbidden)
                if e.status == 403:
                    continue
                # Re-raise other errors
                raise
        
        return {
            "total_namespaces": len(analytics),
            "analytics": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/rbac/summary")
async def get_rbac_summary() -> dict:
    """Get RBAC configuration summary"""
    try:
        roles = rbac_v1.list_role_for_all_namespaces()
        cluster_roles = rbac_v1.list_cluster_role()
        role_bindings = rbac_v1.list_role_binding_for_all_namespaces()
        cluster_role_bindings = rbac_v1.list_cluster_role_binding()
        
        # Analyze role complexity
        role_rules = defaultdict(int)
        for role in roles.items:
            if role.rules:
                role_rules[role.metadata.namespace] += len(role.rules)
        
        return {
            "roles": {
                "total": len(roles.items),
                "cluster_roles": len(cluster_roles.items),
                "namespace_distribution": dict(role_rules)
            },
            "bindings": {
                "role_bindings": len(role_bindings.items),
                "cluster_role_bindings": len(cluster_role_bindings.items)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except client.exceptions.ApiException as e:
        if e.status == 403:
            return {
                "error": "ServiceAccount lacks RBAC permissions to view cluster roles",
                "requires": "get, list on roles, clusterroles, rolebindings, clusterrolebindings"
            }
        raise HTTPException(status_code=e.status, detail=str(e))

@app.get("/api/analytics/serviceaccounts/{namespace}")
async def get_serviceaccount_permissions(namespace: str) -> dict:
    """Analyze ServiceAccount permissions in a namespace"""
    try:
        serviceaccounts = v1.list_namespaced_service_account(namespace)
        role_bindings = rbac_v1.list_namespaced_role_binding(namespace)
        
        sa_permissions = {}
        for sa in serviceaccounts.items:
            sa_name = sa.metadata.name
            bound_roles = []
            
            for rb in role_bindings.items:
                for subject in rb.subjects or []:
                    if subject.kind == "ServiceAccount" and subject.name == sa_name:
                        bound_roles.append({
                            "binding": rb.metadata.name,
                            "role": rb.role_ref.name,
                            "role_kind": rb.role_ref.kind
                        })
            
            sa_permissions[sa_name] = {
                "namespace": namespace,
                "role_bindings": bound_roles,
                "binding_count": len(bound_roles)
            }
        
        return {
            "namespace": namespace,
            "serviceaccounts": sa_permissions,
            "total": len(sa_permissions)
        }
        
    except client.exceptions.ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise HTTPException(status_code=e.status, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
