#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Running load test..."

INGESTER_URL="http://localhost:8080"
TOTAL_REQUESTS=1000
CONCURRENT=10

# Check if port-forward is already running
if pgrep -f "kubectl port-forward.*log-ingester" > /dev/null; then
    echo "Port-forward already running, using existing connection"
    PF_PID=$(pgrep -f "kubectl port-forward.*log-ingester" | head -1)
else
    # Port forward to log-ingester
    kubectl port-forward -n log-analytics svc/log-ingester 8080:8000 &
    PF_PID=$!
    sleep 5
fi

echo "Generating $TOTAL_REQUESTS log entries with $CONCURRENT concurrent connections..."

generate_log() {
    local level=("DEBUG" "INFO" "WARN" "ERROR")
    local source=("web-server" "api-gateway" "database" "cache" "worker")
    
    curl -s -X POST "$INGESTER_URL/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"level\": \"${level[$RANDOM % ${#level[@]}]}\",
            \"message\": \"Test log entry $(date +%s)\",
            \"source\": \"${source[$RANDOM % ${#source[@]}]}\",
            \"host\": \"test-host-$RANDOM\"
        }" > /dev/null
}

export -f generate_log
export INGESTER_URL

# Run concurrent requests
seq $TOTAL_REQUESTS | xargs -P $CONCURRENT -I {} bash -c 'generate_log'

echo "Load test complete! Generated $TOTAL_REQUESTS log entries."

# Cleanup
kill $PF_PID
