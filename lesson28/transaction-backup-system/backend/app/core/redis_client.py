"""Redis client for caching"""
import redis
import os
import logging

logger = logging.getLogger(__name__)

_redis_client = None

def get_redis_client():
    """Get Redis client singleton"""
    global _redis_client
    
    if _redis_client is None:
        try:
            redis_host = os.getenv("REDIS_HOST", "redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            _redis_client = None
    
    return _redis_client
