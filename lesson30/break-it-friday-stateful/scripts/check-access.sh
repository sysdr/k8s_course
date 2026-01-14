#!/bin/bash

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Checking Service Access${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get WSL IP
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "unknown")

echo -e "${YELLOW}Service Status:${NC}"
echo ""

# Check API
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database API is running${NC}"
    echo "   Local: http://localhost:8000"
    if [ "$WSL_IP" != "unknown" ]; then
        echo "   WSL IP: http://${WSL_IP}:8000"
    fi
else
    echo -e "${RED}✗ Database API is not running${NC}"
fi

# Check Frontend
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
    echo "   Local: http://localhost:3000"
    if [ "$WSL_IP" != "unknown" ]; then
        echo "   WSL IP: http://${WSL_IP}:3000"
    fi
else
    echo -e "${RED}✗ Frontend is not running${NC}"
fi

echo ""
echo -e "${YELLOW}Access from Windows:${NC}"
echo "  If localhost doesn't work, try:"
if [ "$WSL_IP" != "unknown" ]; then
    echo "    http://${WSL_IP}:8000 (API)"
    echo "    http://${WSL_IP}:3000 (Dashboard)"
else
    echo "    Find WSL IP with: hostname -I"
fi

echo ""
echo -e "${YELLOW}Port Status:${NC}"
netstat -tuln 2>/dev/null | grep -E ':(8000|3000)' || ss -tuln 2>/dev/null | grep -E ':(8000|3000)' || echo "  No services listening"

echo ""
echo -e "${BLUE}To access from Windows browser:${NC}"
echo "  1. Try: http://localhost:3000"
echo "  2. If that fails, use WSL IP: http://${WSL_IP}:3000"
echo "  3. Make sure Windows Firewall allows connections"
echo ""
