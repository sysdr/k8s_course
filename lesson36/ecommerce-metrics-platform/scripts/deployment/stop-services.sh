#!/bin/bash
set -euo pipefail

echo "=== Stopping Services ==="

# Stop by PID file if it exists
if [ -f /tmp/ecommerce-service-pids.txt ]; then
    PIDS=$(cat /tmp/ecommerce-service-pids.txt)
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping process $PID"
            kill $PID
        fi
    done
    rm -f /tmp/ecommerce-service-pids.txt
fi

# Also kill by port
for port in 8000 8001; do
    PID=$(lsof -ti :$port 2>/dev/null || true)
    if [ ! -z "$PID" ]; then
        echo "Stopping service on port $port (PID: $PID)"
        kill $PID 2>/dev/null || true
    fi
done

echo "=== Services Stopped ==="
