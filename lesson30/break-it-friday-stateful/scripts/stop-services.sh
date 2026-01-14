#!/bin/bash

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Break-It-Friday services...${NC}"

# Stop Database API
if [ -f /tmp/database-api.pid ]; then
    PID=$(cat /tmp/database-api.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Stopped Database API (PID: $PID)${NC}"
    fi
    rm -f /tmp/database-api.pid
fi

# Stop Frontend
if [ -f /tmp/frontend.pid ]; then
    PID=$(cat /tmp/frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Stopped Frontend (PID: $PID)${NC}"
    fi
    rm -f /tmp/frontend.pid
fi

# Kill any remaining processes
pkill -f "python3.*app.py" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining API processes${NC}" || true
pkill -f "python3.*http.server.*3000" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining frontend processes${NC}" || true

# Kill port-forwards if any
pkill -f "kubectl port-forward" 2>/dev/null && echo -e "${GREEN}✓ Stopped port-forwards${NC}" || true

echo -e "${GREEN}All services stopped${NC}"
