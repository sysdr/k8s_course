#!/bin/bash

# Quick script to restart just the API with fixes

set -euo pipefail

echo "Restarting Database API with fixes..."

# Stop existing API
pkill -f "python3 app.py" 2>/dev/null || true
sleep 1

# Start API
cd "$(dirname "$0")/../apps/database-api"
nohup python3 app.py > /tmp/database-api.log 2>&1 &
echo $! > /tmp/database-api.pid

echo "Waiting for API to start..."
for i in {1..10}; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ API is running on port 8000"
        echo "  Health: http://localhost:8000/health"
        echo "  All Services: http://localhost:8000/health/all"
        exit 0
    fi
    sleep 1
done

echo "✗ API failed to start. Check /tmp/database-api.log"
cat /tmp/database-api.log | tail -10
exit 1
