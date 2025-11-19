#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Stopping all microservices..."

# Kill processes by PID files
for pidfile in "${PROJECT_ROOT}/logs"/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        service=$(basename "$pidfile" .pid)
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            rm "$pidfile"
        fi
    fi
done

# Kill by process name as fallback
pkill -f "uvicorn.*app:app" 2>/dev/null || true
pkill -f "react-scripts.*start" 2>/dev/null || true

echo "All services stopped."
