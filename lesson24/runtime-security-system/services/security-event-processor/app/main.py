from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import httpx
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Security Event Processor", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SeverityLevel(str, Enum):
    DEBUG = "DEBUG"; INFO = "INFO"; WARNING = "WARNING"; ERROR = "ERROR"; CRITICAL = "CRITICAL"

class ThreatCategory(str, Enum):
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"; SUSPICIOUS_FILE_ACCESS = "SUSPICIOUS_FILE_ACCESS"
    NETWORK_ANOMALY = "NETWORK_ANOMALY"; PROCESS_SPAWNING = "PROCESS_SPAWNING"
    CONTAINER_BREAKOUT = "CONTAINER_BREAKOUT"; CRYPTOMINING = "CRYPTOMINING"

class FalcoEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rule: str; priority: SeverityLevel; output: str; hostname: str
    container_id: Optional[str] = None; container_name: Optional[str] = None
    namespace: Optional[str] = None; pod_name: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict)

class SecurityEvent(BaseModel):
    event_id: str; falco_event: FalcoEvent; risk_score: float
    threat_category: ThreatCategory; recommended_action: str
    containment_applied: bool = False; analysis_metadata: Dict[str, Any] = Field(default_factory=dict)

security_events: List[SecurityEvent] = []
event_stats = defaultdict(int)

def calculate_risk_score(event: FalcoEvent) -> float:
    base = {SeverityLevel.DEBUG: 10, SeverityLevel.INFO: 20, SeverityLevel.WARNING: 40, 
            SeverityLevel.ERROR: 70, SeverityLevel.CRITICAL: 95}.get(event.priority, 50)
    if event.namespace in ["kube-system", "kube-public", "default"]: base += 15
    if any(t in event.output.lower() for t in ["privileged", "root", "sudo"]): base += 10
    if any(p in event.output for p in ["/etc/", "/root/", "/proc/", "/sys/"]): base += 10
    return min(base, 100.0)

def categorize_threat(event: FalcoEvent) -> ThreatCategory:
    r, o = event.rule.lower(), event.output.lower()
    if any(t in r or t in o for t in ["privilege", "sudo"]): return ThreatCategory.PRIVILEGE_ESCALATION
    if any(t in r for t in ["spawn", "exec", "shell"]): return ThreatCategory.PROCESS_SPAWNING
    if any(t in r or t in o for t in ["file", "write"]): return ThreatCategory.SUSPICIOUS_FILE_ACCESS
    if any(t in r or t in o for t in ["network", "connect"]): return ThreatCategory.NETWORK_ANOMALY
    if any(t in r or t in o for t in ["breakout", "escape"]): return ThreatCategory.CONTAINER_BREAKOUT
    if any(t in o for t in ["crypto", "mining"]): return ThreatCategory.CRYPTOMINING
    return ThreatCategory.SUSPICIOUS_FILE_ACCESS

def recommend_action(risk_score: float) -> str:
    if risk_score >= 90: return "IMMEDIATE_ISOLATION_AND_TERMINATION"
    if risk_score >= 70: return "AUTOMATIC_NETWORK_ISOLATION"
    if risk_score >= 50: return "ALERT_SECURITY_TEAM"
    return "LOG_AND_MONITOR"

async def trigger_incident_response(event: SecurityEvent):
    if event.risk_score < 70: return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post("http://incident-response-service:8000/api/v1/incidents/trigger",
                json={"event_id": event.event_id, "pod_name": event.falco_event.pod_name,
                      "namespace": event.falco_event.namespace, "action": event.recommended_action,
                      "risk_score": event.risk_score})
            if r.status_code == 200: event.containment_applied = True; event_stats["containment"] += 1
    except Exception as e: logger.error(f"Incident response failed: {e}")

@app.post("/api/v1/events/ingest", response_model=SecurityEvent)
async def ingest_event(event: FalcoEvent, bg: BackgroundTasks):
    risk = calculate_risk_score(event)
    category = categorize_threat(event)
    action = recommend_action(risk)
    
    sec_event = SecurityEvent(event_id=f"evt-{int(datetime.utcnow().timestamp()*1000)}",
        falco_event=event, risk_score=risk, threat_category=category, recommended_action=action,
        analysis_metadata={"processed_at": datetime.utcnow().isoformat()})
    
    security_events.append(sec_event)
    if len(security_events) > 1000: security_events.pop(0)
    
    event_stats["total"] += 1; event_stats[f"sev_{event.priority}"] += 1
    event_stats[f"cat_{category}"] += 1
    if risk >= 70: event_stats["high_risk"] += 1; bg.add_task(trigger_incident_response, sec_event)
    
    logger.info(f"Event: {event.rule[:40]} | Risk: {risk:.0f} | {category} | {action}")
    return sec_event

@app.get("/api/v1/events", response_model=List[SecurityEvent])
async def get_events(limit: int = 100): return security_events[-limit:]

@app.get("/api/v1/statistics")
async def get_stats():
    return {"total": event_stats["total"], "high_risk": event_stats["high_risk"],
            "containment": event_stats.get("containment", 0)}

@app.get("/health")
async def health(): return {"status": "healthy", "events": event_stats["total"]}

@app.get("/ready")
async def ready(): return {"status": "ready", "events": event_stats["total"]}

if __name__ == "__main__":
    import uvicorn; uvicorn.run(app, host="0.0.0.0", port=8000)
