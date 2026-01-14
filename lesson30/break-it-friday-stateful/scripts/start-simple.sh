#!/bin/bash

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Starting Break-It-Friday Services${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 is not installed${NC}"
    exit 1
fi

# Install required packages
echo -e "${YELLOW}Installing Python packages...${NC}"
python3 -m pip install --break-system-packages --quiet fastapi uvicorn[standard] psycopg2-binary redis pydantic python-multipart 2>&1 | grep -v "already satisfied" || true

# Start Database API
echo -e "${YELLOW}Starting Database API on port 8000...${NC}"

# Check if already running
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database API already running${NC}"
else
    cd "${BASE_DIR}/apps/database-api"
    
    # Start API in background
    # Use localhost for Docker databases
    POSTGRES_HOST=localhost REDIS_HOST=localhost nohup python3 app.py > /tmp/database-api.log 2>&1 &
    API_PID=$!
    echo $API_PID > /tmp/database-api.pid
    
    # Wait for API to be ready
    echo -e "${YELLOW}Waiting for API to start...${NC}"
    for i in {1..30}; do
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Database API started (PID: $API_PID)${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Database API failed to start. Check /tmp/database-api.log${NC}"
            cat /tmp/database-api.log | tail -10
            exit 1
        fi
        sleep 1
    done
fi

# Start Frontend
echo -e "${YELLOW}Starting Frontend on port 3000...${NC}"

# Check if already running
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend already running${NC}"
else
    cd "${BASE_DIR}/apps/frontend/public"
    
    # Start simple HTTP server
    nohup python3 -m http.server 3000 > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/frontend.pid
    
    sleep 2
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend starting... (may take a moment)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Services are running!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Access points:${NC}"
echo "  📊 Dashboard: ${GREEN}http://localhost:3000${NC}"
echo "  🔌 API: ${GREEN}http://localhost:8000${NC}"
echo "  ❤️  Health: ${GREEN}http://localhost:8000/health${NC}"
echo "  📈 All Services: ${GREEN}http://localhost:8000/health/all${NC}"
echo ""
echo -e "${BLUE}To stop services:${NC}"
echo "  ./stop-services.sh"
echo "  or: kill \$(cat /tmp/database-api.pid) \$(cat /tmp/frontend.pid)"
echo ""

# Test API
echo -e "${YELLOW}Testing API...${NC}"
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "{}")
if [ "$HEALTH" != "{}" ]; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${RED}✗ API not responding properly${NC}"
fi

echo ""
echo -e "${GREEN}Ready! Open http://localhost:3000 in your browser${NC}"
