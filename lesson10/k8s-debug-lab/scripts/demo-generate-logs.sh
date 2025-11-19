#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

API_URL="${API_URL:-http://localhost:8002}"
INGESTER_URL="${INGESTER_URL:-http://localhost:8000}"

echo "Generating demo log data..."
echo ""

# Check if API is running
if ! curl -s -f "${API_URL}/health" > /dev/null 2>&1; then
    echo "Error: Log API is not running at ${API_URL}"
    echo "Please start services first: ./scripts/startup-all.sh"
    exit 1
fi

# Generate sample logs
generate_log() {
    local level=$1
    local source=$2
    local message=$3
    
    curl -s -X POST "${INGESTER_URL}/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"level\": \"${level}\",
            \"source\": \"${source}\",
            \"message\": \"${message}\",
            \"metadata\": {\"demo\": true, \"timestamp\": \"$(date -Iseconds)\"}
        }" > /dev/null
}

# Generate logs from different sources
sources=("web-server" "api-gateway" "auth-service" "database" "cache-service")
levels=("DEBUG" "INFO" "WARNING" "ERROR" "CRITICAL")
messages=(
    "User login successful"
    "Database connection established"
    "Cache miss for key: user:123"
    "Request timeout after 30s"
    "Memory usage at 85%"
    "Authentication failed for user"
    "Query executed in 45ms"
    "Failed to connect to external API"
    "Session expired"
    "Data validation error"
)

echo "Sending logs to ingester..."
for i in {1..50}; do
    source=${sources[$((RANDOM % ${#sources[@]}))]}
    level=${levels[$((RANDOM % ${#levels[@]}))]}
    message=${messages[$((RANDOM % ${#messages[@]}))]}
    
    generate_log "$level" "$source" "$message"
    
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Sent $i logs..."
    fi
done

echo ""
echo "✓ Generated 50 log entries"
echo ""
echo "Waiting for processing..."
sleep 3

echo ""
echo "Checking dashboard metrics..."
summary=$(curl -s "${API_URL}/api/v1/summary")
echo "$summary" | python3 -m json.tool 2>/dev/null || echo "$summary"

echo ""
echo "Dashboard should now show updated metrics at: http://localhost:3000"
