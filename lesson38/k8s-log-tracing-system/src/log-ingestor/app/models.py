"""Pydantic schemas for the log-ingestor API surface."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    DEBUG = "DEBUG"
    INFO  = "INFO"
    WARN  = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class LogEvent(BaseModel):
    """Inbound log payload."""
    timestamp: datetime            = Field(default_factory=datetime.utcnow)
    severity:  Severity            = Severity.INFO
    service:   str                 = Field(..., min_length=1, max_length=128)
    message:   str                 = Field(..., max_length=4096)
    metadata:  Optional[dict]      = None
    trace_id:  Optional[str]       = None   # filled by OTel if missing
    span_id:   Optional[str]       = None


class LogEventResponse(BaseModel):
    event_id: str
    accepted: bool
    trace_id: str
