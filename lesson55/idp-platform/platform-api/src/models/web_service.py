"""Pydantic models for Platform API."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RuntimeType(str, Enum):
    python3_11 = "python3.11"
    nodejs20 = "nodejs20"
    go1_21 = "go1.21"

class ScalingSpec(BaseModel):
    minReplicas: int = Field(1, ge=1, le=100)
    maxReplicas: int = Field(10, ge=1, le=1000)
    targetCPU: int = Field(70, ge=1, le=100)

class ResourceTier(BaseModel):
    tier: str = "standard"

class NetworkingSpec(BaseModel):
    public: bool = False
    domains: List[str] = Field(default_factory=list)

class ObservabilitySpec(BaseModel):
    metrics: bool = True
    tracing: bool = False

class WebServiceSpec(BaseModel):
    name: str
    team: str
    repository: str
    runtime: RuntimeType = RuntimeType.python3_11
    scaling: ScalingSpec = Field(default_factory=ScalingSpec)
    resources: ResourceTier = Field(default_factory=ResourceTier)
    networking: NetworkingSpec = Field(default_factory=NetworkingSpec)
    observability: ObservabilitySpec = Field(default_factory=ObservabilitySpec)

class WebServiceStatus(BaseModel):
    name: str
    team: str
    status: str
    message: Optional[str] = None
    resources_created: Optional[dict] = None
    timestamp: Optional[datetime] = None

class TeamProvisionRequest(BaseModel):
    team_name: str
    quota_tier: str = "default"
