"""
RBAC Validator Service - Tests and validates RBAC policies
Requires RBAC: create on selfsubjectaccessreviews and selfsubjectrulesreviews
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from pydantic import BaseModel
from typing import List, Optional
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RBAC Validator Service")

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

auth_v1 = client.AuthorizationV1Api()

class PermissionCheck(BaseModel):
    namespace: Optional[str] = None
    resource: str
    verb: str
    subresource: Optional[str] = None
    service_account: Optional[str] = None  # Optional: check permissions for a specific SA
    sa_namespace: Optional[str] = None  # Namespace of the ServiceAccount

class PermissionResult(BaseModel):
    resource: str
    verb: str
    allowed: bool
    reason: Optional[str]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "rbac-validator"}

@app.post("/api/rbac/validate")
async def validate_permission(check: PermissionCheck) -> PermissionResult:
    """Validate a specific permission using SelfSubjectAccessReview or SubjectAccessReview"""
    try:
        resource_attr = client.V1ResourceAttributes(
            namespace=check.namespace,
            verb=check.verb,
            resource=check.resource
        )
        
        if check.subresource:
            resource_attr.subresource = check.subresource
        
        # If a ServiceAccount is specified, use SubjectAccessReview to check permissions for that SA
        # Otherwise, use SelfSubjectAccessReview (checks permissions for rbac-validator-sa)
        if check.service_account and check.sa_namespace:
            # Use SubjectAccessReview to check permissions for a specific ServiceAccount
            sar = client.V1SubjectAccessReview(
                spec=client.V1SubjectAccessReviewSpec(
                    resource_attributes=resource_attr,
                    user=f"system:serviceaccount:{check.sa_namespace}:{check.service_account}"
                )
            )
            response = auth_v1.create_subject_access_review(sar)
        else:
            # Use SelfSubjectAccessReview (checks permissions for the ServiceAccount making the call)
            sar = client.V1SelfSubjectAccessReview(
                spec=client.V1SelfSubjectAccessReviewSpec(
                    resource_attributes=resource_attr
                )
            )
            response = auth_v1.create_self_subject_access_review(sar)
        
        return PermissionResult(
            resource=check.resource,
            verb=check.verb,
            allowed=response.status.allowed,
            reason=response.status.reason
        )
        
    except Exception as e:
        logger.error(f"Error validating permission: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rbac/list-permissions")
async def list_my_permissions(namespace: Optional[str] = None) -> dict:
    """List all permissions for current ServiceAccount"""
    try:
        ssr = client.V1SelfSubjectRulesReview(
            spec=client.V1SelfSubjectRulesReviewSpec(
                namespace=namespace
            )
        )
        
        response = auth_v1.create_self_subject_rules_review(ssr)
        
        # Parse rules
        permissions = []
        for rule in response.status.resource_rules:
            permissions.append({
                "resources": rule.resources,
                "verbs": rule.verbs,
                "api_groups": rule.api_groups or [""],
                "resource_names": rule.resource_names or []
            })
        
        return {
            "namespace": namespace or "cluster-wide",
            "permission_count": len(permissions),
            "permissions": permissions,
            "incomplete": response.status.incomplete,
            "evaluation_error": response.status.evaluation_error or "none"
        }
        
    except Exception as e:
        logger.error(f"Error listing permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rbac/bulk-validate")
async def bulk_validate(checks: List[PermissionCheck]) -> dict:
    """Validate multiple permissions at once"""
    results = []
    
    for check in checks:
        try:
            result = await validate_permission(check)
            results.append({
                "resource": check.resource,
                "verb": check.verb,
                "namespace": check.namespace,
                "allowed": result.allowed,
                "reason": result.reason
            })
        except Exception as e:
            results.append({
                "resource": check.resource,
                "verb": check.verb,
                "namespace": check.namespace,
                "allowed": False,
                "error": str(e)
            })
    
    allowed_count = sum(1 for r in results if r.get("allowed", False))
    
    return {
        "total_checks": len(results),
        "allowed": allowed_count,
        "denied": len(results) - allowed_count,
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
