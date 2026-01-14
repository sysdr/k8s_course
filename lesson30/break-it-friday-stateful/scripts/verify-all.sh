#!/bin/bash

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Complete System Verification${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

ALL_GOOD=true

# Check services are running
echo -e "${YELLOW}1. Checking Services...${NC}"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ Database API is running${NC}"
else
    echo -e "${RED}   ✗ Database API is NOT running${NC}"
    ALL_GOOD=false
fi

if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ Frontend is running${NC}"
else
    echo -e "${RED}   ✗ Frontend is NOT running${NC}"
    ALL_GOOD=false
fi

# Check metrics are non-zero
echo ""
echo -e "${YELLOW}2. Checking Metrics...${NC}"
HEALTH_DATA=$(curl -s http://localhost:8000/health/all 2>/dev/null || echo "{}")

if [ "$HEALTH_DATA" != "{}" ]; then
    PG_LATENCY=$(echo "$HEALTH_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('services', {}).get('postgresql', {}).get('latency_ms', 0))" 2>/dev/null || echo "0")
    REDIS_LATENCY=$(echo "$HEALTH_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('services', {}).get('redis', {}).get('latency_ms', 0))" 2>/dev/null || echo "0")
    OVERALL=$(echo "$HEALTH_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('overall_status', 'unknown'))" 2>/dev/null || echo "unknown")
    
    if [ "$PG_LATENCY" != "0" ] && [ -n "$PG_LATENCY" ]; then
        echo -e "${GREEN}   ✓ PostgreSQL latency: ${PG_LATENCY}ms (non-zero)${NC}"
    else
        echo -e "${RED}   ✗ PostgreSQL latency is zero${NC}"
        ALL_GOOD=false
    fi
    
    if [ "$REDIS_LATENCY" != "0" ] && [ -n "$REDIS_LATENCY" ]; then
        echo -e "${GREEN}   ✓ Redis latency: ${REDIS_LATENCY}ms (non-zero)${NC}"
    else
        echo -e "${RED}   ✗ Redis latency is zero${NC}"
        ALL_GOOD=false
    fi
    
    if [ "$OVERALL" != "unknown" ] && [ -n "$OVERALL" ]; then
        echo -e "${GREEN}   ✓ Overall status: ${OVERALL}${NC}"
    else
        echo -e "${RED}   ✗ Overall status is missing${NC}"
        ALL_GOOD=false
    fi
else
    echo -e "${RED}   ✗ Could not fetch health data${NC}"
    ALL_GOOD=false
fi

# Check no duplicates
echo ""
echo -e "${YELLOW}3. Checking for Duplicates...${NC}"
PYTHON_COUNT=$(ps aux | grep -E "python.*app\.py" | grep -v grep | wc -l)
HTTP_COUNT=$(ps aux | grep -E "python.*http.server.*3000" | grep -v grep | wc -l)

if [ "$PYTHON_COUNT" -le 1 ]; then
    echo -e "${GREEN}   ✓ Python services: ${PYTHON_COUNT} (no duplicates)${NC}"
else
    echo -e "${RED}   ✗ Found ${PYTHON_COUNT} Python services (duplicates!)${NC}"
    ALL_GOOD=false
fi

if [ "$HTTP_COUNT" -le 1 ]; then
    echo -e "${GREEN}   ✓ HTTP servers: ${HTTP_COUNT} (no duplicates)${NC}"
else
    echo -e "${RED}   ✗ Found ${HTTP_COUNT} HTTP servers (duplicates!)${NC}"
    ALL_GOOD=false
fi

# Check ports
echo ""
echo -e "${YELLOW}4. Checking Ports...${NC}"
if (netstat -tuln 2>/dev/null || ss -tuln 2>/dev/null) | grep -q ":8000"; then
    echo -e "${GREEN}   ✓ Port 8000 is listening${NC}"
else
    echo -e "${RED}   ✗ Port 8000 is NOT listening${NC}"
    ALL_GOOD=false
fi

if (netstat -tuln 2>/dev/null || ss -tuln 2>/dev/null) | grep -q ":3000"; then
    echo -e "${GREEN}   ✓ Port 3000 is listening${NC}"
else
    echo -e "${RED}   ✗ Port 3000 is NOT listening${NC}"
    ALL_GOOD=false
fi

# Summary
echo ""
echo -e "${BLUE}================================${NC}"
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    echo ""
    echo -e "${GREEN}Dashboard is ready!${NC}"
    echo "  Access at: http://localhost:3000"
    echo "  Or WSL IP: http://172.17.32.19:3000"
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
    echo ""
    echo "Run: ./start-simple.sh to start services"
    exit 1
fi
