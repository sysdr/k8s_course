#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Checking service status..."
echo ""

check_service() {
    local name=$1
    local port=$2
    local url=$3
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✓ $name: Running on port $port (healthy)"
            return 0
        else
            echo "⚠ $name: Running on port $port (not responding)"
            return 1
        fi
    else
        echo "✗ $name: Not running"
        return 1
    fi
}

check_service "Log Ingester" 8000 "http://localhost:8000/health"
check_service "Log Processor" 8001 "http://localhost:8001/health"
check_service "Log API" 8002 "http://localhost:8002/health"

echo ""
echo "Checking for duplicate processes..."
duplicates=$(pgrep -f "uvicorn.*app:app" | wc -l)
if [ "$duplicates" -gt 3 ]; then
    echo "⚠ Warning: Multiple service processes detected"
    pgrep -f "uvicorn.*app:app" | xargs ps -p
else
    echo "✓ No duplicate services detected"
fi
