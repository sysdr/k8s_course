#!/usr/bin/env python3
import json
import os
import time
from collections import defaultdict
from datetime import datetime

LOG_FILE = os.getenv('LOG_FILE', '/data/logs/app.log')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', '/data/processed/metrics.json')
METRICS_FILE = os.getenv('METRICS_FILE', '/data/metrics/metrics.json')

def process_logs():
    metrics = {
        "total_logs": 0,
        "by_level": defaultdict(int),
        "by_source": defaultdict(int),
        "last_processed": None
    }
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    metrics["total_logs"] += 1
                    metrics["by_level"][entry.get("level", "UNKNOWN")] += 1
                    metrics["by_source"][entry.get("source", "unknown")] += 1
                    metrics["last_processed"] = entry.get("timestamp")
                except:
                    continue
    
    metrics["by_level"] = dict(metrics["by_level"])
    metrics["by_source"] = dict(metrics["by_source"])
    metrics["timestamp"] = datetime.utcnow().isoformat()
    
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics

if __name__ == '__main__':
    while True:
        process_logs()
        time.sleep(5)
