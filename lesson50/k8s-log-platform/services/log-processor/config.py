"""Service configuration for log processor."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_brokers: str = "kafka:9092"
    kafka_topic: str = "log-events"
    consumer_group: str = "log-processor-group"
    database_url: str = "postgresql://loguser:logpass@postgres:5432/logdb"
    redis_url: str = "redis://redis:6379"

    class Config:
        env_prefix = "LOG_PROCESSOR_"
