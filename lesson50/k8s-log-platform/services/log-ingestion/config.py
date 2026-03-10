"""Service configuration via environment variables."""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_brokers: str = "kafka:9092"
    kafka_topic: str = "log-events"
    max_batch_size: int = 1000
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_prefix = "LOG_INGESTION_"
        env_file = ".env"
