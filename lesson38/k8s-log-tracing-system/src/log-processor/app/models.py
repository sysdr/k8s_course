"""ORM models — persisted log events."""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from .database import Base


class LogRecord(Base):
    __tablename__ = "log_records"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    event_id  = Column(String(36), unique=True, nullable=False, index=True)
    trace_id  = Column(String(32), index=True)
    severity  = Column(String(8),  nullable=False)
    service   = Column(String(128), nullable=False, index=True)
    message   = Column(Text, nullable=False)
    event_metadata  = Column("metadata", Text)  # JSON blob (renamed to avoid SQLAlchemy conflict)
    created_at= Column(DateTime, default=datetime.utcnow)
