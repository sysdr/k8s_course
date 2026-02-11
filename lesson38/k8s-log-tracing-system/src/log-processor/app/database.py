"""SQLAlchemy engine + session factory, instrumented with OTel."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://app:changeme@postgres.messaging.svc.cluster.local:5432/logs",
)

engine = create_engine(DB_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

# instrument *after* engine creation so every query emits a span
SQLAlchemyInstrumentor().instrument(engine=engine)


class Base(DeclarativeBase):
    pass
