from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import logging
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Incident Response Controller")

try: config.load_incluster_config()
except: config.load_kube_config()

v1 = client.CoreV1Api()
net_v1 = client.NetworkingV1Api()

class IncidentRequest(BaseModel):
    event_id: str; pod_name: str; namespace: str; action: str; risk_score: float

class IncidentResponse(BaseModel):
    incident_id: str; status: str; actions_taken: list; containment_time_ms: float

async def isolate_pod(namespace: str, pod_name: str) -> bool:
    try:
        policy = client.V1NetworkPolicy(
            api_version="networking.k8s.io/v1", kind="NetworkPolicy",
            metadata=client.V1ObjectMeta(name=f"isolate-{pod_name}", namespace=namespace),
            spec=client.V1NetworkPolicySpec(
                pod_selector=client.V1LabelSelector(match_labels={"app": pod_name}),
                policy_types=["Ingress", "Egress"], ingress=[], egress=[]))
        net_v1.create_namespaced_network_policy(namespace, policy)
        logger.info(f"Isolated {pod_name} in {namespace}")
        return True
    except Exception as e:
        if "409" in str(e): return True
        logger.error(f"Isolation failed: {e}")
        return False

@app.post("/api/v1/incidents/trigger", response_model=IncidentResponse)
async def trigger_response(req: IncidentRequest):
    start = datetime.utcnow()
    inc_id = f"inc-{int(start.timestamp())}"
    actions = []
    
    logger.info(f"Incident {inc_id}: {req.action} for {req.pod_name} (risk: {req.risk_score})")
    
    if req.action in ["AUTOMATIC_NETWORK_ISOLATION", "IMMEDIATE_ISOLATION_AND_TERMINATION"]:
        if await isolate_pod(req.namespace, req.pod_name): actions.append("NETWORK_ISOLATED")
    
    if req.action == "IMMEDIATE_ISOLATION_AND_TERMINATION" and req.risk_score >= 90:
        logger.warning(f"CRITICAL: {req.pod_name} requires termination (risk: {req.risk_score})")
        actions.append("TERMINATION_PENDING")
    
    elapsed = (datetime.utcnow() - start).total_seconds() * 1000
    return IncidentResponse(incident_id=inc_id, status="CONTAINED", actions_taken=actions, containment_time_ms=elapsed)

@app.get("/health")
async def health(): return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn; uvicorn.run(app, host="0.0.0.0", port=8000)
