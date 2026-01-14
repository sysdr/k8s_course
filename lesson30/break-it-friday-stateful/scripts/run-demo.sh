#!/bin/bash

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Break-It-Friday Demo Runner${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

API_URL="${API_URL:-http://localhost:8000}"

# Check if API is accessible
echo -e "${YELLOW}Checking API availability...${NC}"
if ! curl -s -f "${API_URL}/health" > /dev/null; then
    echo -e "${RED}ERROR: Cannot connect to API at ${API_URL}${NC}"
    echo "Make sure the database-api service is running"
    exit 1
fi
echo -e "${GREEN}✓ API is accessible${NC}"
echo ""

# Run demo: Simulate database load
echo -e "${YELLOW}Running demo: Simulating database load...${NC}"
echo "This will generate metrics for the dashboard"
echo ""

# Trigger load test
LOAD_DURATION="${LOAD_DURATION:-60}"
echo -e "${YELLOW}Starting load test for ${LOAD_DURATION} seconds...${NC}"

# Start load test in background
curl -s -X POST "${API_URL}/debug/simulate-load?duration_seconds=${LOAD_DURATION}" > /dev/null &
LOAD_PID=$!

# Monitor health checks during load
echo -e "${YELLOW}Monitoring service health...${NC}"
echo ""

for i in $(seq 1 $((LOAD_DURATION / 10))); do
    echo "--- Health Check ${i} ---"
    
    # Check all services
    HEALTH_DATA=$(curl -s "${API_URL}/health/all" || echo "{}")
    
    if [ "$HEALTH_DATA" != "{}" ]; then
        echo "$HEALTH_DATA" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_DATA"
        
        # Extract metrics
        POSTGRES_LATENCY=$(echo "$HEALTH_DATA" | grep -o '"latency_ms":[0-9.]*' | head -1 | cut -d: -f2 || echo "0")
        REDIS_LATENCY=$(echo "$HEALTH_DATA" | grep -o '"latency_ms":[0-9.]*' | tail -1 | cut -d: -f2 || echo "0")
        
        echo "PostgreSQL Latency: ${POSTGRES_LATENCY}ms"
        echo "Redis Latency: ${REDIS_LATENCY}ms"
    else
        echo "Failed to fetch health data"
    fi
    
    echo ""
    sleep 10
done

# Wait for load test to complete
wait $LOAD_PID 2>/dev/null || true

echo ""
echo -e "${GREEN}Demo completed!${NC}"
echo ""
echo "Check the dashboard to see updated metrics:"
echo "  Frontend: http://localhost:3000 (or port-forward URL)"
echo "  API Health: ${API_URL}/health/all"
