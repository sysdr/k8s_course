#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_DIR="${PROJECT_ROOT}/services/log-api"

if [ ! -d "$SERVICE_DIR" ]; then
    echo "Error: Service directory not found: $SERVICE_DIR"
    exit 1
fi

cd "$SERVICE_DIR"

# Check if service is already running
if pgrep -f "uvicorn.*log-api" > /dev/null || pgrep -f "app:app.*8002" > /dev/null; then
    echo "Warning: Log API service may already be running"
    echo "Checking processes..."
    ps aux | grep -E "uvicorn|app:app" | grep -v grep || true
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt

echo "Starting Log API Service on port 8002..."
python app.py
