from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://loguser:logpass@postgres:5432/logdb"
    redis_url: str = "redis://redis:6379"

    class Config:
        env_prefix = "LOG_QUERY_"
