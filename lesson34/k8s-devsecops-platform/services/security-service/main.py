"""
Security Service - Provides comprehensive security metrics and monitoring
Includes: Vulnerability scanning, Policy violations, Runtime threats, Network security, Secrets, Audit logs
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import random
import os

app = FastAPI(
    title="Security Service",
    description="DevSecOps Security Metrics and Monitoring",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory data stores (use databases in production)
vulnerability_store: deque = deque(maxlen=1000)
policy_violations: deque = deque(maxlen=1000)
runtime_threats: deque = deque(maxlen=1000)
network_events: deque = deque(maxlen=1000)
secret_access_logs: deque = deque(maxlen=1000)
audit_logs: deque = deque(maxlen=10000)

# Initialize with some demo data
def init_demo_data():
    """Initialize with realistic demo data"""
    now = datetime.now()
    
    # Vulnerability scanning results
    critical_cves = [
        {"cve_id": "CVE-2024-1234", "severity": "CRITICAL", "package": "openssl", "version": "1.1.1", "fixed_version": "1.1.1k", "image": "api-gateway:latest", "status": "blocked"},
        {"cve_id": "CVE-2024-5678", "severity": "CRITICAL", "package": "nginx", "version": "1.20.0", "fixed_version": "1.20.1", "image": "frontend:latest", "status": "blocked"},
        {"cve_id": "CVE-2024-9012", "severity": "HIGH", "package": "python", "version": "3.9.0", "fixed_version": "3.9.18", "image": "auth-service:latest", "status": "blocked"},
    ]
    
    high_cves = [
        {"cve_id": "CVE-2024-3456", "severity": "HIGH", "package": "requests", "version": "2.25.1", "fixed_version": "2.28.0", "image": "analytics-service:latest", "status": "blocked"},
        {"cve_id": "CVE-2024-7890", "severity": "HIGH", "package": "urllib3", "version": "1.26.0", "fixed_version": "1.26.5", "image": "log-processor:latest", "status": "blocked"},
    ]
    
    for cve in critical_cves + high_cves:
        cve["scanned_at"] = (now - timedelta(hours=random.randint(1, 24))).isoformat()
        vulnerability_store.append(cve)
    
    # Policy violations
    violations = [
        {"policy": "require-non-root-user", "resource": "deployment/frontend", "namespace": "devsecops", "violation": "Container running as root", "mode": "enforce", "blocked": True, "timestamp": (now - timedelta(minutes=30)).isoformat()},
        {"policy": "require-resource-limits", "resource": "deployment/api-gateway", "namespace": "devsecops", "violation": "Missing memory limits", "mode": "audit", "blocked": False, "timestamp": (now - timedelta(hours=2)).isoformat()},
        {"policy": "disallow-privileged", "resource": "pod/test-pod", "namespace": "devsecops", "violation": "Privileged container detected", "mode": "enforce", "blocked": True, "timestamp": (now - timedelta(minutes=15)).isoformat()},
    ]
    
    for violation in violations:
        policy_violations.append(violation)
    
    # Runtime threats
    threats = [
        {"alert": "Shell execution detected", "severity": "WARNING", "pod": "api-gateway-7d4f8", "namespace": "devsecops", "process": "/bin/sh", "timestamp": (now - timedelta(minutes=45)).isoformat()},
        {"alert": "Privilege escalation attempt", "severity": "CRITICAL", "pod": "auth-service-9k2m1", "namespace": "devsecops", "process": "sudo", "timestamp": (now - timedelta(hours=1)).isoformat()},
        {"alert": "Suspicious network connection", "severity": "WARNING", "pod": "frontend-3x7p2", "namespace": "devsecops", "process": "curl", "timestamp": (now - timedelta(minutes=20)).isoformat()},
    ]
    
    for threat in threats:
        runtime_threats.append(threat)
    
    # Network security events
    network_events_data = [
        {"type": "allowed", "source": "frontend", "destination": "api-gateway", "policy": "frontend-to-gateway", "timestamp": (now - timedelta(minutes=5)).isoformat()},
        {"type": "blocked", "source": "external", "destination": "auth-service", "policy": "default-deny", "timestamp": (now - timedelta(minutes=10)).isoformat()},
        {"type": "allowed", "source": "api-gateway", "destination": "analytics-service", "policy": "gateway-to-analytics", "timestamp": (now - timedelta(minutes=2)).isoformat()},
    ]
    
    for event in network_events_data:
        network_events.append(event)
    
    # Secret access logs
    secret_logs = [
        {"secret": "jwt-secret", "action": "read", "user": "api-gateway", "status": "success", "timestamp": (now - timedelta(minutes=1)).isoformat()},
        {"secret": "jwt-secret", "action": "read", "user": "auth-service", "status": "success", "timestamp": (now - timedelta(minutes=3)).isoformat()},
        {"secret": "jwt-secret", "action": "rotate", "user": "admin", "status": "success", "last_rotation": (now - timedelta(days=7)).isoformat(), "timestamp": (now - timedelta(days=7)).isoformat()},
        {"secret": "db-password", "action": "read", "user": "unauthorized-user", "status": "failed", "timestamp": (now - timedelta(hours=2)).isoformat()},
    ]
    
    for log in secret_logs:
        secret_access_logs.append(log)
    
    # Audit logs
    audit_entries = [
        {"user": "admin", "action": "deploy", "resource": "deployment/api-gateway", "result": "blocked", "reason": "Critical CVE detected", "timestamp": (now - timedelta(hours=3)).isoformat()},
        {"user": "admin", "action": "deploy", "resource": "deployment/frontend", "result": "blocked", "reason": "Policy violation: running as root", "timestamp": (now - timedelta(minutes=30)).isoformat()},
        {"user": "user", "action": "access", "resource": "secret/jwt-secret", "result": "denied", "reason": "Insufficient permissions", "timestamp": (now - timedelta(hours=1)).isoformat()},
        {"user": "admin", "action": "deploy", "resource": "deployment/analytics-service", "result": "allowed", "reason": "All checks passed", "timestamp": (now - timedelta(days=1)).isoformat()},
    ]
    
    for entry in audit_entries:
        audit_logs.append(entry)

# Initialize demo data
init_demo_data()

# Models
class VulnerabilitySummary(BaseModel):
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    blocked_deployments: int
    total_scanned: int

class PolicyViolationSummary(BaseModel):
    total_violations: int
    blocked_deployments: int
    audit_mode_count: int
    enforce_mode_count: int
    top_policies: List[Dict[str, Any]]

class RuntimeThreatSummary(BaseModel):
    critical_alerts: int
    warning_alerts: int
    affected_pods: int
    recent_threats: List[Dict[str, Any]]

class NetworkSecuritySummary(BaseModel):
    allowed_connections: int
    blocked_connections: int
    policy_hits: int
    encrypted_traffic_percent: float
    recent_events: List[Dict[str, Any]]

class SecretsSummary(BaseModel):
    total_access: int
    failed_attempts: int
    last_rotation: Optional[str]
    recent_access: List[Dict[str, Any]]

class AuditSummary(BaseModel):
    total_events: int
    blocked_actions: int
    allowed_actions: int
    recent_events: List[Dict[str, Any]]

class SecurityDashboard(BaseModel):
    vulnerabilities: VulnerabilitySummary
    policy_violations: PolicyViolationSummary
    runtime_threats: RuntimeThreatSummary
    network_security: NetworkSecuritySummary
    secrets: SecretsSummary
    audit: AuditSummary

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "security-service"}

@app.get("/vulnerabilities", response_model=VulnerabilitySummary)
async def get_vulnerabilities():
    """Get vulnerability scanning results"""
    critical = [v for v in vulnerability_store if v["severity"] == "CRITICAL"]
    high = [v for v in vulnerability_store if v["severity"] == "HIGH"]
    medium = [v for v in vulnerability_store if v["severity"] == "MEDIUM"]
    low = [v for v in vulnerability_store if v["severity"] == "LOW"]
    blocked = [v for v in vulnerability_store if v.get("status") == "blocked"]
    
    return VulnerabilitySummary(
        critical_count=len(critical),
        high_count=len(high),
        medium_count=len(medium),
        low_count=len(low),
        blocked_deployments=len(blocked),
        total_scanned=len(vulnerability_store)
    )

@app.get("/vulnerabilities/list")
async def list_vulnerabilities(severity: Optional[str] = None):
    """List all vulnerabilities, optionally filtered by severity"""
    vulns = list(vulnerability_store)
    if severity:
        vulns = [v for v in vulns if v["severity"] == severity.upper()]
    return {"vulnerabilities": vulns}

@app.get("/policy-violations", response_model=PolicyViolationSummary)
async def get_policy_violations():
    """Get policy violation summary"""
    violations = list(policy_violations)
    blocked = [v for v in violations if v.get("blocked", False)]
    audit_mode = [v for v in violations if v.get("mode") == "audit"]
    enforce_mode = [v for v in violations if v.get("mode") == "enforce"]
    
    # Count violations by policy
    policy_counts = defaultdict(int)
    for v in violations:
        policy_counts[v["policy"]] += 1
    
    top_policies = [{"policy": k, "count": v} for k, v in sorted(policy_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    return PolicyViolationSummary(
        total_violations=len(violations),
        blocked_deployments=len(blocked),
        audit_mode_count=len(audit_mode),
        enforce_mode_count=len(enforce_mode),
        top_policies=top_policies
    )

@app.get("/policy-violations/list")
async def list_policy_violations():
    """List all policy violations"""
    return {"violations": list(policy_violations)}

@app.get("/runtime-threats", response_model=RuntimeThreatSummary)
async def get_runtime_threats():
    """Get runtime threat detection summary"""
    threats = list(runtime_threats)
    critical = [t for t in threats if t["severity"] == "CRITICAL"]
    warning = [t for t in threats if t["severity"] == "WARNING"]
    
    affected_pods = len(set(t["pod"] for t in threats))
    recent = sorted(threats, key=lambda x: x["timestamp"], reverse=True)[:10]
    
    return RuntimeThreatSummary(
        critical_alerts=len(critical),
        warning_alerts=len(warning),
        affected_pods=affected_pods,
        recent_threats=recent
    )

@app.get("/network-security", response_model=NetworkSecuritySummary)
async def get_network_security():
    """Get network security metrics"""
    events = list(network_events)
    allowed = [e for e in events if e["type"] == "allowed"]
    blocked = [e for e in events if e["type"] == "blocked"]
    
    # Calculate encrypted traffic (simulated - 95% in zero trust setup)
    encrypted_percent = 95.0
    
    recent = sorted(events, key=lambda x: x["timestamp"], reverse=True)[:10]
    
    return NetworkSecuritySummary(
        allowed_connections=len(allowed),
        blocked_connections=len(blocked),
        policy_hits=len(events),
        encrypted_traffic_percent=encrypted_percent,
        recent_events=recent
    )

@app.get("/secrets", response_model=SecretsSummary)
async def get_secrets_activity():
    """Get secrets management activity"""
    logs = list(secret_access_logs)
    failed = [l for l in logs if l.get("status") == "failed"]
    
    # Find last rotation
    rotations = [l for l in logs if l.get("action") == "rotate"]
    last_rotation = rotations[0]["last_rotation"] if rotations else None
    
    recent = sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:10]
    
    return SecretsSummary(
        total_access=len(logs),
        failed_attempts=len(failed),
        last_rotation=last_rotation,
        recent_access=recent
    )

@app.get("/audit", response_model=AuditSummary)
async def get_audit_logs():
    """Get audit and compliance logs"""
    logs = list(audit_logs)
    blocked = [l for l in logs if l.get("result") == "blocked" or l.get("result") == "denied"]
    allowed = [l for l in logs if l.get("result") == "allowed"]
    
    recent = sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:20]
    
    return AuditSummary(
        total_events=len(logs),
        blocked_actions=len(blocked),
        allowed_actions=len(allowed),
        recent_events=recent
    )

@app.get("/dashboard", response_model=SecurityDashboard)
async def get_security_dashboard():
    """Get complete security dashboard data"""
    return SecurityDashboard(
        vulnerabilities=await get_vulnerabilities(),
        policy_violations=await get_policy_violations(),
        runtime_threats=await get_runtime_threats(),
        network_security=await get_network_security(),
        secrets=await get_secrets_activity(),
        audit=await get_audit_logs()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
