"""Pydantic models for log ingestion."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class LogEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service: str = Field(..., min_length=1, max_length=128)
    level: str = Field(..., pattern=r"^(DEBUG|INFO|WARN|ERROR|FATAL)$")
    message: str = Field(..., min_length=1, max_length=8192)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("level")
    @classmethod
    def normalize_level(cls, v: str) -> str:
        return v.upper()


class LogEventBatch(BaseModel):
    events: List[LogEvent] = Field(..., min_length=1)


class HealthResponse(BaseModel):
    status: str
    kafka_connected: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
