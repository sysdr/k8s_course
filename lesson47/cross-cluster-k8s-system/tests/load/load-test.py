"""
Load testing script for cross-cluster logging system
Generates realistic log traffic to test scalability
"""
import asyncio
import aiohttp
import random
from datetime import datetime
import json

CLUSTER_A_URL = "http://localhost:8000"  # Update with actual LoadBalancer IP
SERVICES = ["api-gateway", "user-service", "payment-service", "notification-service"]
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
WEIGHTS = [10, 60, 20, 8, 2]  # Probability weights

async def generate_log():
    """Generate a realistic log entry"""
    return {
        "service": random.choice(SERVICES),
        "level": random.choices(LOG_LEVELS, weights=WEIGHTS)[0],
        "message": f"Sample log message {random.randint(1000, 9999)}",
        "trace_id": f"trace-{random.randint(100000, 999999)}",
        "metadata": {
            "user_id": random.randint(1, 10000),
            "request_id": f"req-{random.randint(100000, 999999)}"
        }
    }

async def send_log(session, log):
    """Send a log to the ingestion service"""
    try:
        async with session.post(f"{CLUSTER_A_URL}/ingest", json=log) as response:
            return response.status == 202
    except Exception as e:
        print(f"Error: {e}")
        return False

async def load_test(duration_seconds=60, logs_per_second=100):
    """Run load test"""
    print(f"Starting load test: {logs_per_second} logs/sec for {duration_seconds}s")
    
    async with aiohttp.ClientSession() as session:
        start_time = datetime.now()
        total_sent = 0
        total_success = 0
        
        while (datetime.now() - start_time).seconds < duration_seconds:
            tasks = []
            for _ in range(logs_per_second):
                log = await generate_log()
                tasks.append(send_log(session, log))
            
            results = await asyncio.gather(*tasks)
            total_sent += len(results)
            total_success += sum(results)
            
            await asyncio.sleep(1)
        
        print(f"Load test complete!")
        print(f"Total sent: {total_sent}")
        print(f"Success: {total_success}")
        print(f"Success rate: {(total_success/total_sent)*100:.2f}%")

if __name__ == "__main__":
    asyncio.run(load_test(duration_seconds=60, logs_per_second=50))
