#!/usr/bin/env python3
import requests
import json

# Test the API endpoints
base_url = "http://api-service:8002"

print("Testing API endpoints...")
print("=" * 50)

# Test stats
print("\n1. Testing /stats endpoint:")
try:
    response = requests.get(f"{base_url}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test logs for web-app
print("\n2. Testing /logs/web-app endpoint:")
try:
    response = requests.get(f"{base_url}/logs/web-app?limit=20")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Service: {data.get('service')}")
    print(f"Count: {data.get('count')}")
    print(f"Logs returned: {len(data.get('logs', []))}")
    if data.get('logs'):
        print("\nFirst 3 logs:")
        for log in data.get('logs', [])[:3]:
            print(f"  - {log.get('level')}: {log.get('message')}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
