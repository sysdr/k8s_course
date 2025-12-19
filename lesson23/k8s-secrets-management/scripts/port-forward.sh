#!/bin/bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Change to project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if port-forward is already running
if pgrep -f "kubectl port-forward.*frontend" > /dev/null; then
    echo "Port-forward is already running. Stopping it..."
    pkill -f "kubectl port-forward.*frontend"
    sleep 2
fi

# Try port 80 first, fall back to 8080 if 80 is in use
PORT=80
if lsof -i :80 > /dev/null 2>&1 || netstat -tlnp 2>/dev/null | grep -q ":80 " || ss -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "Port 80 is in use. Using port 8080 instead."
    PORT=8080
fi

echo "Setting up port-forward for frontend on port $PORT..."
echo "Dashboard will be available at: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop the port-forward"

kubectl port-forward -n secrets-platform svc/frontend ${PORT}:80

