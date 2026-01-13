#!/usr/bin/env python3
import redis
import json
import time

# Connect to Redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)

# Current timestamp
now = int(time.time())

# Add log entries
logs = [
    {"service": "web-app", "level": "INFO", "message": "User logged in successfully", "timestamp": "2026-01-13T10:40:01Z"},
    {"service": "web-app", "level": "ERROR", "message": "Database connection failed", "timestamp": "2026-01-13T10:39:00Z"},
    {"service": "api-service", "level": "INFO", "message": "API request processed successfully", "timestamp": "2026-01-13T10:40:02Z"},
    {"service": "web-app", "level": "WARNING", "message": "High memory usage detected", "timestamp": "2026-01-13T10:39:10Z"},
    {"service": "web-app", "level": "INFO", "message": "Cache updated", "timestamp": "2026-01-13T10:40:03Z"},
    {"service": "api-service", "level": "INFO", "message": "Health check passed", "timestamp": "2026-01-13T10:40:04Z"},
    {"service": "web-app", "level": "ERROR", "message": "Failed to process payment", "timestamp": "2026-01-13T10:39:01Z"},
    {"service": "web-app", "level": "ERROR", "message": "Timeout connecting to external service", "timestamp": "2026-01-13T10:39:02Z"},
    {"service": "web-app", "level": "ERROR", "message": "Invalid user input validation failed", "timestamp": "2026-01-13T10:39:03Z"},
    {"service": "web-app", "level": "ERROR", "message": "Session expired", "timestamp": "2026-01-13T10:39:04Z"},
    {"service": "web-app", "level": "ERROR", "message": "File upload failed", "timestamp": "2026-01-13T10:39:05Z"},
    {"service": "web-app", "level": "INFO", "message": "Order placed successfully", "timestamp": "2026-01-13T10:40:05Z"},
    {"service": "api-service", "level": "INFO", "message": "Request rate: 150 req/min", "timestamp": "2026-01-13T10:40:06Z"},
    {"service": "web-app", "level": "INFO", "message": "Email sent to user", "timestamp": "2026-01-13T10:40:07Z"},
    {"service": "web-app", "level": "WARNING", "message": "Slow query detected", "timestamp": "2026-01-13T10:39:20Z"},
]

for i, log in enumerate(logs):
    service = log["service"]
    level = log["level"]
    key = f"logs:{service}:{level}"
    score = now + i
    value = json.dumps(log)
    r.zadd(key, {value: score})
    print(f"Added {service} {level}: {log['message']}")

print(f"\nAdded {len(logs)} log entries to Redis")
print("Refresh your dashboard to see the logs!")
