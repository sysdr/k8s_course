"""
Worker Service - Processes background jobs
This service intentionally has drift for debugging exercise
"""
import os
import time
import logging
import redis
from prometheus_client import Counter, Gauge, start_http_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
JOBS_PROCESSED = Counter('jobs_processed_total', 'Total jobs processed')
ACTIVE_WORKERS = Gauge('active_workers', 'Number of active workers')

def main():
    """Main worker loop"""
    logger.info("Worker service starting...")
    
    # Start Prometheus metrics server
    start_http_server(8001)
    logger.info("Metrics server started on port 8001")
    
    # Connect to Redis
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    
    try:
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        r.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return
    
    ACTIVE_WORKERS.set(1)
    
    # Process jobs
    logger.info("Worker ready to process jobs...")
    while True:
        try:
            # Simulate job processing
            job = r.lpop("jobs:queue")
            if job:
                logger.info(f"Processing job: {job}")
                time.sleep(1)  # Simulate work
                JOBS_PROCESSED.inc()
                logger.info(f"Job completed: {job}")
            else:
                time.sleep(5)  # Wait for jobs
        except KeyboardInterrupt:
            logger.info("Shutting down worker...")
            ACTIVE_WORKERS.set(0)
            break
        except Exception as e:
            logger.error(f"Error processing job: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
