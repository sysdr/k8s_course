#!/bin/bash

# Fix Windows access to WSL services

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Windows Access Fix${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get WSL IP
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "unknown")

echo -e "${YELLOW}WSL IP Address: ${WSL_IP}${NC}"
echo ""

# Check if services are running
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is running on port 8000${NC}"
else
    echo -e "${YELLOW}⚠ API is not running. Starting...${NC}"
    cd "$(dirname "$0")/.."
    bash scripts/start-simple.sh > /dev/null 2>&1
    sleep 3
fi

if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running on port 3000${NC}"
else
    echo -e "${YELLOW}⚠ Frontend is not running. Starting...${NC}"
    cd "$(dirname "$0")/.."
    bash scripts/start-simple.sh > /dev/null 2>&1
    sleep 3
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Access URLs${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${YELLOW}From Windows Browser:${NC}"
echo ""
echo -e "  Option 1 (Try first):"
echo -e "    ${GREEN}http://localhost:3000${NC} (Dashboard)"
echo -e "    ${GREEN}http://localhost:8000${NC} (API)"
echo ""
echo -e "  Option 2 (If localhost doesn't work):"
echo -e "    ${GREEN}http://${WSL_IP}:3000${NC} (Dashboard)"
echo -e "    ${GREEN}http://${WSL_IP}:8000${NC} (API)"
echo ""
echo -e "${YELLOW}To configure Windows port forwarding (run in PowerShell as Admin):${NC}"
echo ""
echo "netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=${WSL_IP}"
echo "netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=${WSL_IP}"
echo ""
echo -e "${YELLOW}To remove port forwarding (if needed):${NC}"
echo ""
echo "netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0"
echo "netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0"
echo ""
echo -e "${BLUE}================================${NC}"
