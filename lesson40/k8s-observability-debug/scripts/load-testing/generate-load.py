#!/usr/bin/env python3
"""
Generate realistic load on log-processor to produce metrics
"""
import asyncio
import aiohttp
import random
import time
from datetime import datetime

LOG_LEVELS = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
LOG_SOURCES = ["api-gateway", "auth-service", "database", "cache", "queue"]

async def send_log_entry(session, url):
    """Send a single log entry"""
    log_entry = {
        "level": random.choice(LOG_LEVELS),
        "message": f"Sample log message at {datetime.now().isoformat()}",
        "source": random.choice(LOG_SOURCES),
        "metadata": {
            "request_id": f"req-{random.randint(1000, 9999)}",
            "user_id": f"user-{random.randint(1, 100)}"
        }
    }
    
    try:
        async with session.post(f"{url}/logs/ingest", json=log_entry) as response:
            return response.status
    except Exception as e:
        print(f"Error: {e}")
        return 500

async def generate_load(duration_seconds=300, requests_per_second=10):
    """Generate continuous load"""
    url = "http://localhost:8000"  # Update if using different URL
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        request_count = 0
        
        print(f"Starting load generation: {requests_per_second} req/s for {duration_seconds}s")
        
        while time.time() - start_time < duration_seconds:
            batch_start = time.time()
            
            # Send batch of requests
            tasks = [send_log_entry(session, url) for _ in range(requests_per_second)]
            results = await asyncio.gather(*tasks)
            
            request_count += len(results)
            success_count = sum(1 for r in results if r == 200)
            
            if request_count % 100 == 0:
                print(f"Sent {request_count} requests, {success_count}/{len(results)} successful")
            
            # Sleep to maintain desired rate
            elapsed = time.time() - batch_start
            sleep_time = max(0, 1.0 - elapsed)
            await asyncio.sleep(sleep_time)
        
        print(f"\nCompleted: {request_count} total requests")

if __name__ == "__main__":
    asyncio.run(generate_load(duration_seconds=300, requests_per_second=10))
