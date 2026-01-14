#!/bin/bash

# Complete restart script - databases + API + frontend

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Complete System Restart${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Step 1: Stop everything
echo -e "${YELLOW}Step 1: Stopping all services...${NC}"
"${SCRIPT_DIR}/stop-services.sh" > /dev/null 2>&1

# Step 2: Deploy databases
echo -e "${YELLOW}Step 2: Deploying databases...${NC}"
"${SCRIPT_DIR}/deploy-databases-docker.sh" > /dev/null 2>&1

# Step 3: Start API and frontend
echo -e "${YELLOW}Step 3: Starting API and frontend...${NC}"
"${SCRIPT_DIR}/start-simple.sh" 2>&1 | tail -10

# Step 4: Verify
echo ""
echo -e "${YELLOW}Step 4: Verifying services...${NC}"
sleep 3
"${SCRIPT_DIR}/verify-databases.sh"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}System Restarted!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Access:"
echo "  Dashboard: http://localhost:3000"
echo "  API: http://localhost:8000/health/all"
echo ""
