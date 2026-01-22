#!/bin/bash
# Start the E-Commerce Metrics Dashboard

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/services/frontend"

echo "=== Starting E-Commerce Metrics Dashboard ==="
echo ""

# Check if order service is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  WARNING: Order service is not running on port 8000"
    echo "   Start it with: ./scripts/deployment/start-services.sh"
    echo ""
fi

cd "$FRONTEND_DIR"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install --legacy-peer-deps
fi

echo "Starting React development server..."
echo ""
echo "🌐 Dashboard URLs:"
echo "   Local:    http://localhost:3000"
echo "   Network:  http://172.17.32.19:3000"
echo ""
echo "📝 Note: If accessing from Windows browser, use the Network URL"
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the dashboard
BROWSER=none PORT=3000 npm start
