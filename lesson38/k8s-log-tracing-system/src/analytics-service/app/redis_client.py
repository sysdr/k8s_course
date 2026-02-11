"""Redis connection pool with OTel span wrapping for every command."""
import os
import redis
from opentelemetry import trace

REDIS_URL = os.getenv("REDIS_URL", "redis://redis.messaging.svc.cluster.local:6379/0")

pool = redis.ConnectionPool.from_url(REDIS_URL, max_connections=20, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=pool, decode_responses=True)


class TracedRedis:
    """Thin wrapper that wraps each Redis call in an OTel span."""

    def __init__(self):
        self._redis = get_redis()
        self._tracer = trace.get_tracer("analytics-service.redis")

    def get(self, key: str):
        with self._tracer.start_as_current_span("redis.get") as span:
            span.set_attribute("db.redis.key", key)
            return self._redis.get(key)

    def set(self, key: str, value, ex: int | None = None):
        with self._tracer.start_as_current_span("redis.set") as span:
            span.set_attribute("db.redis.key", key)
            return self._redis.set(key, value, ex=ex)

    def incr(self, key: str):
        with self._tracer.start_as_current_span("redis.incr") as span:
            span.set_attribute("db.redis.key", key)
            return self._redis.incr(key)

    def hset(self, name: str, mapping: dict):
        with self._tracer.start_as_current_span("redis.hset") as span:
            span.set_attribute("db.redis.key", name)
            return self._redis.hset(name, mapping=mapping)

    def hgetall(self, name: str):
        with self._tracer.start_as_current_span("redis.hgetall") as span:
            span.set_attribute("db.redis.key", name)
            return self._redis.hgetall(name)
    
    def lrange(self, name: str, start: int, end: int):
        with self._tracer.start_as_current_span("redis.lrange") as span:
            span.set_attribute("db.redis.key", name)
            return self._redis.lrange(name, start, end)
    
    def llen(self, name: str):
        with self._tracer.start_as_current_span("redis.llen") as span:
            span.set_attribute("db.redis.key", name)
            return self._redis.llen(name)