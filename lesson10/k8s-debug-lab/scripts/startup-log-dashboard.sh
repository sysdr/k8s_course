#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_DIR="${PROJECT_ROOT}/services/log-dashboard"

if [ ! -d "$SERVICE_DIR" ]; then
    echo "Error: Service directory not found: $SERVICE_DIR"
    exit 1
fi

cd "$SERVICE_DIR"

# Check if service is already running
if pgrep -f "react-scripts.*start" > /dev/null || pgrep -f "node.*react-scripts" > /dev/null; then
    echo "Warning: Log dashboard service may already be running"
    echo "Checking processes..."
    ps aux | grep -E "react-scripts|node" | grep -v grep || true
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo "Starting Log Dashboard Service on port 3000..."
export REACT_APP_API_URL="${REACT_APP_API_URL:-http://localhost:8002}"
npm start
