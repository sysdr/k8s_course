"""
Platform API - Internal Developer Platform
Production-grade API for Kubernetes orchestration and developer self-service
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from kubernetes import client, config
import logging
import os
from typing import List, Optional
from datetime import datetime
import asyncio

from models.web_service import WebServiceSpec, WebServiceStatus, TeamProvisionRequest
from services.k8s_orchestrator import KubernetesOrchestrator
from services.namespace_manager import NamespaceManager
from controllers.platform_controller import PlatformController

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
api_requests_total = Counter(
    'platform_api_requests_total', 
    'Total API requests', 
    ['method', 'endpoint', 'status']
)
api_request_duration = Histogram(
    'platform_api_request_duration_seconds', 
    'API request latency'
)
services_created_total = Counter(
    'platform_services_created_total', 
    'Total services created', 
    ['team', 'runtime']
)
namespaces_provisioned_total = Counter(
    'platform_namespaces_provisioned_total',
    'Total team namespaces provisioned'
)

# Initialize FastAPI app
app = FastAPI(
    title="Internal Developer Platform API",
    description="Production-grade platform for Kubernetes self-service",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security - accept any Bearer token for demo/local dev (no auth required when no token sent)
def get_optional_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    if credentials is None:
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials="demo-token")
    return credentials
security = get_optional_token

# Initialize Kubernetes client
try:
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes configuration")
    k8s_client = client.ApiClient()
except config.ConfigException:
    try:
        config.load_kube_config()
        logger.info("Loaded kubeconfig configuration")
        k8s_client = client.ApiClient()
    except Exception as e:
        logger.warning("Kubernetes not available (local dev): %s", e)
        k8s_client = None
orchestrator = KubernetesOrchestrator(k8s_client)
namespace_manager = NamespaceManager(k8s_client)
platform_controller = PlatformController(k8s_client)

###############################################################################
# Health and Monitoring Endpoints
###############################################################################

@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check - validates Kubernetes connectivity"""
    if k8s_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "error": "Kubernetes not configured"}
        )
    try:
        v1 = client.CoreV1Api(k8s_client)
        namespaces = v1.list_namespace(limit=1)
        return {
            "status": "ready",
            "kubernetes_connected": True,
            "cluster_version": namespaces.metadata.resource_version
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "error": str(e)}
        )

@app.get("/metrics", tags=["monitoring"], response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest().decode('utf-8')

###############################################################################
# Service Management Endpoints
###############################################################################

@app.post(
    "/api/v1/services",
    response_model=WebServiceStatus,
    status_code=status.HTTP_201_CREATED,
    tags=["services"]
)
async def create_service(
    service_spec: WebServiceSpec,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new web service deployment
    
    Orchestrates the creation of:
    - Deployment with security contexts and resource limits
    - Service for internal networking
    - Ingress for external access (if public)
    - HorizontalPodAutoscaler for scaling
    - NetworkPolicy for isolation
    - ServiceMonitor for Prometheus (if metrics enabled)
    - PodDisruptionBudget for high availability
    """
    try:
        logger.info(
            f"Creating service: {service_spec.name} "
            f"for team: {service_spec.team} "
            f"runtime: {service_spec.runtime}"
        )
        
        # Validate team namespace exists
        namespace_name = f"team-{service_spec.team}"
        if not namespace_manager.namespace_exists(namespace_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team namespace not found: {namespace_name}. Please provision team first."
            )
        
        # Check team quota
        if not namespace_manager.check_quota(service_spec.team):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Team {service_spec.team} has exceeded resource quota"
            )
        
        # Generate Kubernetes manifests
        manifests = orchestrator.generate_manifests(service_spec)
        
        # Apply manifests to cluster
        result = await orchestrator.apply_manifests_async(manifests, service_spec.team)
        
        # Update metrics
        services_created_total.labels(
            team=service_spec.team,
            runtime=service_spec.runtime.value
        ).inc()
        
        api_requests_total.labels(
            method="POST",
            endpoint="/api/v1/services",
            status="success"
        ).inc()
        
        return WebServiceStatus(
            name=service_spec.name,
            team=service_spec.team,
            status="creating",
            message="Service deployment initiated successfully",
            resources_created=result["resources_created"],
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service creation failed: {e}", exc_info=True)
        api_requests_total.labels(
            method="POST",
            endpoint="/api/v1/services",
            status="error"
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service creation failed: {str(e)}"
        )

@app.get(
    "/api/v1/services/{team}/{service_name}",
    response_model=WebServiceStatus,
    tags=["services"]
)
async def get_service_status(
    team: str,
    service_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current status of a deployed service"""
    try:
        status_info = await orchestrator.get_service_status_async(team, service_name)
        return status_info
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service not found: {service_name} in team {team}"
        )

@app.get("/api/v1/services", tags=["services"])
async def list_services(
    team: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List all services, optionally filtered by team"""
    try:
        services = await orchestrator.list_services_async(team)
        return {"services": services, "total": len(services)}
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/api/v1/services/{team}/{service_name}", tags=["services"])
async def delete_service(
    team: str,
    service_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a service and all associated resources"""
    try:
        logger.info(f"Deleting service: {service_name} for team: {team}")
        result = await orchestrator.delete_service_async(team, service_name)
        return {
            "message": f"Service {service_name} deleted successfully",
            "details": result
        }
    except Exception as e:
        logger.error(f"Service deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

###############################################################################
# Team/Namespace Management Endpoints
###############################################################################

@app.post(
    "/api/v1/teams",
    status_code=status.HTTP_201_CREATED,
    tags=["teams"]
)
async def provision_team_namespace(
    team_request: TeamProvisionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Provision a new team namespace with quotas and policies
    
    Creates:
    - Namespace with appropriate labels
    - ResourceQuota for capacity limits
    - LimitRange for container defaults
    - NetworkPolicy for tenant isolation
    - ServiceAccount with RBAC permissions
    - RoleBinding for team access
    """
    try:
        logger.info(f"Provisioning namespace for team: {team_request.team_name}")
        
        # Check if namespace already exists
        if namespace_manager.namespace_exists(f"team-{team_request.team_name}"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Team namespace already exists: {team_request.team_name}"
            )
        
        # Provision team resources
        result = await namespace_manager.provision_team_async(
            team_request.team_name,
            team_request.quota_tier
        )
        
        # Update metrics
        namespaces_provisioned_total.inc()
        
        return {
            "team": team_request.team_name,
            "namespace": result["namespace"],
            "resources_created": result["resources"],
            "quota_tier": team_request.quota_tier,
            "status": "provisioned"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Team provisioning failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/teams/{team_name}/quota", tags=["teams"])
async def get_team_quota(
    team_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current resource quota usage for a team"""
    try:
        quota_info = await namespace_manager.get_quota_status_async(team_name)
        return quota_info
    except Exception as e:
        logger.error(f"Failed to get quota info: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team not found: {team_name}"
        )

@app.get("/api/v1/teams", tags=["teams"])
async def list_teams(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List all platform-managed teams"""
    try:
        teams = await namespace_manager.list_teams_async()
        return {"teams": teams, "total": len(teams)}
    except Exception as e:
        logger.error(f"Failed to list teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

###############################################################################
# Platform Statistics and Monitoring
###############################################################################

@app.get("/api/v1/platform/stats", tags=["platform"])
async def get_platform_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get platform-wide statistics and health metrics"""
    try:
        stats = await platform_controller.get_platform_stats_async()
        return stats
    except Exception as e:
        logger.error(f"Failed to get platform stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/platform/health", tags=["platform"])
async def get_platform_health(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed platform health status"""
    try:
        health = await platform_controller.get_platform_health_async()
        return health
    except Exception as e:
        logger.error(f"Failed to get platform health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

###############################################################################
# Application startup and shutdown events
###############################################################################

@app.on_event("startup")
async def startup_event():
    """Initialize platform on startup"""
    logger.info("Platform API starting up...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Kubernetes API accessible: {k8s_client is not None}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Platform API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    )
